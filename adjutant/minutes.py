"""Minutes: the record of the day, from plain sentences, with no model call.

Pattern 3. Minutes as data, with supersede and strike instead of delete.

"I decided ...", "I owe Dana ...", "Sam owes me ...", "note: ...". A correction
supersedes an entry and "scratch that" strikes one; the original always stays.
"""

import re
from datetime import timedelta

from . import clock

SCHEMA = """
CREATE TABLE IF NOT EXISTS minutes (
    id INTEGER PRIMARY KEY,
    time TEXT NOT NULL,
    day TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('note', 'decision', 'promise', 'waiting', 'blocker', 'done', 'idea')),
    text TEXT NOT NULL,
    who TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'superseded', 'struck')),
    replaces INTEGER REFERENCES minutes(id),
    instruction TEXT NOT NULL,
    changed_at TEXT
);
CREATE INDEX IF NOT EXISTS minutes_day ON minutes(day, id);
"""

OPEN_KINDS = ("promise", "waiting", "blocker")
LABELS = {"decision": "DECISIONS", "promise": "YOU PROMISED", "waiting": "WAITING ON OTHERS",
          "blocker": "BLOCKED", "done": "DONE", "note": "NOTES", "idea": "IDEAS"}

# (pattern on the first sentence, kind, group holding the text, group holding "who" or None)
CAPTURE = [
    (r"(?:note|log|fyi|for the record)[:,]\s*(.+)", "note", 1, None),
    (r"idea[:,]\s*(.+)", "idea", 1, None),
    (r"decision[:,]\s*(.+)", "decision", 1, None),
    (r"((?:i|we)(?: have|'ve)? (?:decided|agreed) .+)", "decision", 1, None),
    (r"(i (?:owe|promised) ([a-z][\w'-]*(?: [a-z][\w'-]*)?) .+)", "promise", 1, 2),
    (r"((?:i'm |i am )?waiting (?:on|for) ([a-z][\w'-]*(?: [a-z][\w'-]*)?)\b.*)", "waiting", 1, 2),
    (r"(([a-z][\w'-]*(?: [a-z][\w'-]*)?) owes me .+)", "waiting", 1, 2),
    (r"(([a-z][\w'-]*(?: [a-z][\w'-]*)?) is blocked (?:on|until|by) .+)", "blocker", 1, 2),
]


def capture(text):
    """(kind, text, who) if the first sentence is a minute, else None. Questions never are."""
    first = re.split(r"(?<=[.!])\s", text.strip(), maxsplit=1)[0].rstrip(".!")
    if first.endswith("?"):
        return None
    for pattern, kind, text_group, who_group in CAPTURE:
        found = re.fullmatch(pattern, first, re.I)
        if found:
            who = found.group(who_group) if who_group else None
            return kind, found.group(text_group).strip(), who
    return None


def record(connection, kind, text, instruction, who=None, replaces=None):
    with connection:
        cursor = connection.execute(
            "INSERT INTO minutes(time, day, kind, text, who, replaces, instruction) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (clock.now(), clock.today().isoformat(), kind, text, who, replaces, instruction))
    return get(connection, cursor.lastrowid)


def get(connection, minute_id):
    return connection.execute("SELECT * FROM minutes WHERE id = ?", (int(minute_id),)).fetchone()


def last(connection):
    return connection.execute("SELECT * FROM minutes WHERE status = 'active' ORDER BY id DESC LIMIT 1").fetchone()


def set_status(connection, minute_id, status):
    with connection:
        connection.execute("UPDATE minutes SET status = ?, changed_at = ? WHERE id = ?",
                           (status, clock.now(), minute_id))


def correct(connection, old, new_text, instruction):
    """A correction is a new entry that supersedes the old one. Nothing is overwritten."""
    row = record(connection, old["kind"], new_text, instruction, old["who"], replaces=old["id"])
    set_status(connection, old["id"], "superseded")
    return row


def since(connection, days_back):
    start = (clock.today() - timedelta(days=days_back)).isoformat()
    return connection.execute("SELECT * FROM minutes WHERE day >= ? AND status IN ('active', 'resolved') "
                              "ORDER BY id", (start,)).fetchall()


def open_items(connection, who=None):
    sql = f"SELECT * FROM minutes WHERE status = 'active' AND kind IN {OPEN_KINDS}"
    rows = connection.execute(sql + " ORDER BY id").fetchall()
    if who:
        rows = [r for r in rows if (r["who"] or "").lower().startswith(who.lower())]
    return rows


def line(row):
    return f"m{row['id']:<4} {row['text']}" + ("  (resolved)" if row["status"] == "resolved" else "")


def report(rows, empty="Nothing recorded."):
    if not rows:
        return empty
    out = []
    for kind, label in LABELS.items():
        chosen = [r for r in rows if r["kind"] == kind]
        if chosen:
            out.append(label)
            out.extend("  " + line(r) for r in chosen)
    return "\n".join(out)
