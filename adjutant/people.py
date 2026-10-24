"""People: read-only lookups in an oversoul folder (one Markdown profile per person).

oversoul (https://github.com/chrisabraham/oversoul) is a shared memory for several AI
agents, kept as Markdown in a private Git repo. Point Adjutant at your copy:

    echo ~/path/to/your-oversoul > ~/.config/adjutant/people-dir

Adjutant only reads it. Your other agents keep it current.
"""

import re
from pathlib import Path

from . import store


def folder():
    raw = store.secret("people-dir")
    return Path(raw).expanduser() if raw else None


def _files(base):
    for sub in ("people", "projects"):
        yield from sorted((base / sub).glob("*.md"))


def find(name):
    """Profiles whose file name or first heading matches every word of `name`."""
    base = folder()
    if base is None or not base.is_dir():
        return None
    words = [w.lower() for w in re.findall(r"[\w'-]+", name)]
    found = []
    for path in _files(base):
        if path.name in ("README.md", "INDEX.md"):
            continue
        head = path.read_text(encoding="utf-8", errors="replace")[:400].lower()
        haystack = path.stem.lower().replace("-", " ") + " " + head.split("\n", 1)[0]
        if all(w in haystack for w in words):
            found.append(path)
    return found


def who(name, lines=30):
    found = find(name)
    if found is None:
        return ("No people folder is set. Point Adjutant at an oversoul copy:\n"
                "  echo ~/your-oversoul > ~/.config/adjutant/people-dir")
    if not found:
        return f'No profile matches "{name}".'
    if len(found) > 1:
        return "Several profiles match; say more:\n" + "\n".join(f"  {p.relative_to(folder())}" for p in found)
    text = found[0].read_text(encoding="utf-8", errors="replace").splitlines()
    shown = "\n".join(text[:lines])
    more = f"\n… {len(text) - lines} more lines in {found[0]}" if len(text) > lines else ""
    return shown + more
