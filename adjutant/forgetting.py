""""What am I forgetting": deterministic checks, with snoozes that remember why.

Pattern 5. No model call. Each finding has a stable key, so "snooze" can hide that one
finding until a date, with the reason kept beside it, and it comes back on its own.
"""

import json
from datetime import date, timedelta

from . import clock, ledger, minutes

SCHEMA = """
CREATE TABLE IF NOT EXISTS snoozes (
    key TEXT PRIMARY KEY,
    until TEXT NOT NULL,
    reason TEXT NOT NULL,
    time TEXT NOT NULL
);
"""

STALE_OVERDUE_DAYS = 14
PUSHED_TIMES = 3
PROMISE_DAYS = 3
WAITING_DAYS = 5


def _age(iso):
    return (clock.today() - date.fromisoformat(iso[:10])).days


def _pushes(connection, row):
    count = 0
    for event in ledger.history(connection, row):
        if event["event"] == "changed" and "due_date" in json.loads(event["detail"]):
            count += 1
    return count


def findings(connection):
    """[(key, message, suggested command)], snoozed ones left out."""
    found = []
    for row in ledger.due(connection, "<"):
        days = _age(row["due_date"])
        if days >= STALE_OVERDUE_DAYS:
            found.append((f"stale:{row['num']}", f"{ledger.ref(row)} has been overdue {days} days",
                          f"adj push {row['num']} next Monday   (or: adj {row['num']} done)"))
    for row in ledger.open_tasks(connection):
        pushes = _pushes(connection, row)
        if pushes >= PUSHED_TIMES:
            found.append((f"pushed:{row['num']}", f"{ledger.ref(row)} has been pushed {pushes} times",
                          f"adj {row['num']} done   (if it no longer matters)"))
    for row in minutes.open_items(connection):
        days = _age(row["day"])
        if row["kind"] == "promise" and days >= PROMISE_DAYS:
            found.append((f"m:{row['id']}", f"m{row['id']} you promised {days} days ago: {row['text']}",
                          f"adj m{row['id']} resolved   (or add it: adj add {row['text']})"))
        if row["kind"] == "waiting" and days >= WAITING_DAYS:
            found.append((f"m:{row['id']}", f"m{row['id']} waiting {days} days: {row['text']}",
                          f"adj add follow up with {row['who'] or 'them'} tomorrow"))
    snoozed = {r["key"] for r in connection.execute("SELECT key FROM snoozes WHERE until > ?",
                                                    (clock.today().isoformat(),))}
    return [f for f in found if f[0] not in snoozed]


def snooze(connection, number, days, reason):
    """Snooze finding N of the last list for `days`, keeping the reason."""
    from . import store
    keys = store.get_state(connection, "last_findings", [])
    if not 1 <= number <= len(keys):
        return f"There is no finding {number}. Run: adj what am I forgetting"
    until = (clock.today() + timedelta(days=days)).isoformat()
    with connection:
        connection.execute("INSERT INTO snoozes(key, until, reason, time) VALUES (?, ?, ?, ?) "
                           "ON CONFLICT(key) DO UPDATE SET until = excluded.until, reason = excluded.reason, "
                           "time = excluded.time", (keys[number - 1], until, reason, clock.now()))
    return f"Snoozed finding {number} until {clock.describe_day(until)}" + (f" ({reason})." if reason else ".")


def report(connection):
    from . import store
    found = findings(connection)
    store.set_state(connection, "last_findings", [f[0] for f in found])
    if not found:
        return "Nothing slipping that I can see."
    lines = []
    for n, (_, message, command) in enumerate(found, start=1):
        lines += [f"{n}. {message}", f"   → {command}"]
    lines.append("Snooze one: adj snooze 2 for 7 days because waiting on the client")
    return "\n".join(lines)
