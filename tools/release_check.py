#!/usr/bin/env python3
"""Refuse to publish if the tree holds secrets, personal paths, or names on a private denylist.

Pattern 10. Secrets and data that cannot reach git.

    python3 tools/release_check.py                 # checks every file git would publish
    python3 tools/release_check.py --all           # checks every file on disk, tracked or not

Built-in checks catch the generic leaks: API keys and tokens, private keys, absolute home
paths, IP addresses, email addresses other than allowed ones, and database files.

Your own denylist catches the specific ones: client names, server names, your street.
Keep it OUTSIDE the repo, one word or phrase per line (# for comments):

    ~/.config/adjutant/release-denylist.txt     (or set ADJUTANT_DENYLIST)

Exit status 0 means clean; 1 means something was found, and nothing should ship.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_EMAILS = {"noreply@anthropic.com", "you@example.com"}
ALLOWED_IPS = {"127.0.0.1", "0.0.0.0"}
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".woff", ".woff2"}

PATTERNS = [
    ("Anthropic key", re.compile(r"sk-ant-[A-Za-z0-9_-]{16,}")),
    ("OpenAI-style key", re.compile(r"\bsk-[A-Za-z0-9]{32,}")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}")),
    ("AWS key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("long hex secret", re.compile(r"(?i)(?:token|secret|password|api[_-]?key)\s*[=:]\s*['\"]?[0-9a-f]{32,}")),
    ("home path", re.compile(r"/(?:home|Users)/(?!runner\b|you\b|me\b|user\b)[a-z][\w.-]*/")),
    ("IP address", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")),
    ("email address", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
]


def files(everything):
    if not everything:
        try:
            listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                                    cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
            return [ROOT / f for f in listed]
        except (OSError, subprocess.CalledProcessError):
            pass
    return [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts]


def denylist():
    path = Path(os.environ.get("ADJUTANT_DENYLIST") or Path.home() / ".config/adjutant/release-denylist.txt")
    try:
        words = [w.strip() for w in path.read_text(encoding="utf-8").splitlines()]
    except OSError:
        return [], None
    words = [w for w in words if w and not w.startswith("#")]
    # Whole words only, case-insensitive: "Ann" must not match "annual".
    return [(w, re.compile(r"(?<!\w)" + re.escape(w) + r"(?!\w)", re.I)) for w in words], path


def check(path, words):
    problems = []
    rel = path.relative_to(ROOT)
    if path.suffix in (".sqlite3", ".db") or path.name in ("todoist-token", "anthropic-api-key", ".env"):
        return [f"{rel}: a data or secret file is in the tree"]
    if path.suffix.lower() in BINARY or path == Path(__file__).resolve():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    for number, line in enumerate(text.splitlines(), start=1):
        for label, pattern in PATTERNS:
            for found in pattern.findall(line):
                if label == "email address" and found.lower() in ALLOWED_EMAILS:
                    continue
                if label == "IP address" and (found in ALLOWED_IPS or found.count(".") != 3
                                              or any(int(part) > 255 for part in found.split("."))):
                    continue
                problems.append(f"{rel}:{number}: {label}: {found[:60]}")
        for word, pattern in words:
            if pattern.search(line):
                problems.append(f"{rel}:{number}: denylisted: {word}")
    return problems


def main():
    words, source = denylist()
    problems = []
    for path in files("--all" in sys.argv):
        if path.exists():
            problems += check(path, words)
    print(f"Denylist: {source} ({len(words)} entries)" if source else
          "Denylist: none found (only the built-in checks ran). See the docstring to add one.")
    if problems:
        print(f"RELEASE CHECK FAILED: {len(problems)} finding(s). Nothing should ship.")
        print("\n".join("  " + p for p in problems))
        return 1
    print("Release check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
