"""Fail the build if any module references an undefined name (e.g. a helper
used without importing it). Complements check_wiring.py, which only validates
self.X attribute references - this catches bare module/global names like a
forgotten 'helptip' import that would blank a panel at runtime.
"""
import glob
import subprocess
import sys

files = sorted(glob.glob("echoquill/*.py"))
res = subprocess.run([sys.executable, "-m", "pyflakes"] + files,
                     capture_output=True, text=True)
out = res.stdout + res.stderr
bad = [ln for ln in out.splitlines() if "undefined name" in ln]
if bad:
    print("UNDEFINED NAMES FOUND (would crash at runtime):")
    print("\n".join(bad))
    sys.exit(1)
print("NAMES OK - no undefined names in any module.")
