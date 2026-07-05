"""Custom dictionary + learning from corrections.

- Users can add replacements ("kubernetes" for "cooper netties", names, jargon).
- Community-requested: EchoQuill learns from your corrections. When the same
  correction shows up twice, it's suggested/added automatically.

Stored locally in %APPDATA%\\EchoQuill\\dictionary.json - never uploaded.
"""

import json
import re
from collections import Counter

from .config import app_data_dir

DICT_PATH = app_data_dir() / "dictionary.json"


class Dictionary:
    def __init__(self):
        self.replacements = {}        # {"wrong phrase": "right phrase"}
        self._correction_counts = Counter()
        self.load()

    # ---------- persistence ----------

    def load(self):
        try:
            if DICT_PATH.exists():
                with open(DICT_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.replacements = data.get("replacements", {})
                self._correction_counts = Counter(data.get("corrections", {}))
        except Exception:
            self.replacements = {}

    def save(self):
        try:
            with open(DICT_PATH, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "replacements": self.replacements,
                        "corrections": dict(self._correction_counts),
                    },
                    f, indent=2, ensure_ascii=False,
                )
        except Exception:
            pass

    # ---------- editing ----------

    def add(self, wrong: str, right: str):
        wrong = wrong.strip()
        if wrong and right is not None:
            self.replacements[wrong] = right.strip()
            self.save()

    def remove(self, wrong: str):
        self.replacements.pop(wrong, None)
        self.save()

    # ---------- applying ----------

    def apply(self, text: str) -> str:
        """Apply replacements with word boundaries, preserving leading case."""
        for wrong, right in self.replacements.items():
            pattern = re.compile(r"\b" + re.escape(wrong) + r"\b", re.IGNORECASE)

            def _sub(match, right=right):
                found = match.group(0)
                if found[:1].isupper() and right[:1].islower():
                    return right[:1].upper() + right[1:]
                return right

            text = pattern.sub(_sub, text)
        return text

    # ---------- learning from corrections ----------

    def learn(self, original: str, corrected: str, auto_add_after: int = 2):
        """Compare what was transcribed vs what the user fixed it to.

        Word-level diff; each changed pair counts as one observed correction.
        After the same correction is seen `auto_add_after` times, it becomes
        a dictionary entry automatically.
        """
        orig_words = original.split()
        corr_words = corrected.split()
        if not orig_words or not corr_words:
            return
        if abs(len(orig_words) - len(corr_words)) > 3:
            return  # too different - probably a rewrite, not a correction

        import difflib
        matcher = difflib.SequenceMatcher(a=orig_words, b=corr_words)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != "replace":
                continue
            wrong = " ".join(orig_words[i1:i2]).strip(".,!?;: ")
            right = " ".join(corr_words[j1:j2]).strip(".,!?;: ")
            if not wrong or not right or wrong.lower() == right.lower():
                continue
            if len(wrong) > 60 or len(right) > 60:
                continue
            key = f"{wrong.lower()}→{right}"
            self._correction_counts[key] += 1
            if self._correction_counts[key] >= auto_add_after:
                self.replacements[wrong.lower()] = right
        self.save()
