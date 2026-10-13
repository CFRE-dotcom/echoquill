"""Stdlib-only HTTP, used everywhere EchoQuill talks to the network EXCEPT
yt-dlp itself.

Why this exists: yt-dlp monkey-patches the third-party `urllib3` library
(`Urllib3PercentREOverride` in yt_dlp/networking/_requests.py). The `requests`
library rides on urllib3, so once the video engine is loaded in-process, every
`requests` call can fail with "'Urllib3PercentREOverride' object has no
attribute 'sub'". Python's built-in urllib does NOT use urllib3, so routing our
own calls (AI, licensing, OAuth, TTS, feedback, update check) through here makes
them immune to anything yt-dlp does.
"""

import json as _json
import urllib.error
import urllib.parse
import urllib.request


class HttpError(Exception):
    def __init__(self, code, body=""):
        super().__init__(("HTTP %s %s" % (code, body)).strip())
        self.code = code
        self.body = body


def _opener(proxies=None):
    if proxies:
        return urllib.request.build_opener(
            urllib.request.ProxyHandler(proxies))
    return urllib.request.build_opener()


def request(method, url, headers=None, json_body=None, data=None,
            timeout=60, proxies=None):
    """Returns (status_code, body_bytes). Raises HttpError on HTTP >= 400.
    json_body: dict -> JSON body. data: dict -> form-encoded, or raw bytes."""
    hdrs = dict(headers or {})
    body = None
    if json_body is not None:
        body = _json.dumps(json_body).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    elif isinstance(data, dict):
        body = urllib.parse.urlencode(data).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/x-www-form-urlencoded")
    elif isinstance(data, (bytes, bytearray)):
        body = bytes(data)
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in hdrs.items():
        req.add_header(k, v)
    try:
        with _opener(proxies).open(req, timeout=timeout) as resp:
            return (resp.getcode(), resp.read())
    except urllib.error.HTTPError as e:
        try:
            eb = e.read().decode("utf-8", "replace")
        except Exception:
            eb = ""
        raise HttpError(e.code, eb[:300])


def get_json(url, headers=None, timeout=60, proxies=None):
    _c, b = request("GET", url, headers=headers, timeout=timeout,
                    proxies=proxies)
    return _json.loads(b.decode("utf-8", "replace") or "null")


def post_json(url, json_body=None, data=None, headers=None, timeout=60,
              proxies=None):
    """POST and parse a JSON response. Returns {} on empty, {'_text':...} if the
    reply wasn't JSON."""
    _c, b = request("POST", url, headers=headers, json_body=json_body,
                    data=data, timeout=timeout, proxies=proxies)
    txt = b.decode("utf-8", "replace")
    if not txt:
        return {}
    try:
        return _json.loads(txt)
    except Exception:
        return {"_text": txt}


def get_bytes(url, headers=None, timeout=60, proxies=None):
    _c, b = request("GET", url, headers=headers, timeout=timeout,
                    proxies=proxies)
    return b


def download(url, dest_path, headers=None, timeout=120, proxies=None,
             chunk=65536):
    """Stream a URL to a file."""
    req = urllib.request.Request(url, method="GET")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with _opener(proxies).open(req, timeout=timeout) as resp, \
            open(dest_path, "wb") as fh:
        while True:
            c = resp.read(chunk)
            if not c:
                break
            fh.write(c)
