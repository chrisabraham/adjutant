"""The task ledger: Todoist decides what's open; this keeps a permanent local history.

Pattern 1. An outside authority (a real task service) plus a local append-only history.

- Every task gets a short number (#12) the first time it's seen. Numbers never change
  and are never reused, so "#12" means the same task forever.
- Every change is an event in task_events, whether it was made here or in the Todoist
  app. Events are never updated or deleted.
- When Todoist is unreachable, the last saved copy is shown and nothing is changed.
"""

import json

from . import clock, todoist

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    todoist_id TEXT PRIMARY KEY,
    num INTEGER NOT NULL UNIQUE,
    content TEXT NOT NULL,
    project TEXT,
    priority INTEGER NOT NULL DEFAULT 1,
    labels TEXT NOT NULL DEFAULT '[]',
    due_date TEXT,
    due_string TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done')),
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS task_events (
    id INTEGER PRIMARY KEY,
    time TEXT NOT NULL,
    todoist_id TEXT NOT NULL REFERENCES tasks(todoist_id),
    event TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('adjutant', 'todoist')),
    detail TEXT NOT NULL DEFAULT '{}',
    instruction TEXT
);

CREATE INDEX IF NOT EXISTS task_events_task ON task_events(todoist_id, id);
CREATE INDEX IF NOT EXISTS task_events_time ON task_events(time);
"""

TRACKED = ("content", "project", "priority", "labels", "due_date", "due_string")


class NoMatch(Exception):
    pass


class Ambiguous(Exception):
    def __init__(self, rows):
        super().__init__(f"{len(rows)} tasks match")
        self.rows = rows


def _fields(task, project_names):
    due = task.get("due") or {}
    return {
        "content": task.get("content") or "",
        "project": project_names.get(task.get("project_id")),
        # Todoist's API counts priority backwards: 4 is what the app shows as p1.
        "priority": task.get("priority") or 1,
        "labels": json.dumps(sorted(task.get("labels") or [])),
        "due_date": (due.get("date") or "")[:10] or None,
        "due_string": due.get("string"),
    }


def _event(connection, todoist_id, event, source, detail=None, instruction=None):
    connection.execute(
        "INSERT INTO task_events(time, todoist_id, event, source, detail, instruction) VALUES (?, ?, ?, ?, ?, ?)",
        (clock.now(), todoist_id, event, source, json.dumps(detail or {}), instruction))


def _next_num(connection):
    return (connection.execute("SELECT MAX(num) FROM tasks").fetchone()[0] or 0) + 1


def _upsert(connection, task, project_names, source, instruction=None):
    """Save one task from Todoist; record what changed. Returns the stored row."""
    fields = _fields(task, project_names)
    stamp = clock.now()
    old = connection.execute("SELECT * FROM tasks WHERE todoist_id = ?", (task["id"],)).fetchone()
    if old is None:
        connection.execute(
            "INSERT INTO tasks(todoist_id, num, content, project, priority, labels, due_date, due_string, "
            "status, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?)",
            (task["id"], _next_num(connection), *(fields[k] for k in TRACKED), stamp, stamp))
        _event(connection, task["id"], "created", source, fields, instruction)
    else:
        changed = {k: [old[k], fields[k]] for k in TRACKED if old[k] != fields[k]}
        connection.execute(
            "UPDATE tasks SET content=?, project=?, priority=?, labels=?, due_date=?, due_string=?, "
            "status='open', last_seen=? WHERE todoist_id=?",
            (*(fields[k] for k in TRACKED), stamp, task["id"]))
        if old["status"] == "done":
            _event(connection, task["id"], "reopened", source, instruction=instruction)
        if changed:
            _event(connection, task["id"], "changed", source, changed, instruction)
    return connection.execute("SELECT * FROM tasks WHERE todoist_id = ?", (task["id"],)).fetchone()


def _project_names(connection):
    from . import store
    names = store.get_state(connection, "project_names", {})
    if not names:
        names = {p["id"]: p["name"] for p in todoist.projects()}
        store.set_state(connection, "project_names", names)
    return names


def sync(connection):
    """Bring the local copy up to date with Todoist. Raises todoist.TodoistError if unreachable."""
    from . import store
    names = {p["id"]: p["name"] for p in todoist.projects()}
    store.set_state(connection, "project_names", names)
    active = todoist.active_tasks()
    seen = {task["id"] for task in active}
    with connection:
        for task in active:
            _upsert(connection, task, names, "todoist")
        for row in connection.execute("SELECT * FROM tasks WHERE status = 'open'").fetchall():
            if row["todoist_id"] not in seen:
                connection.execute("UPDATE tasks SET status = 'done' WHERE todoist_id = ?", (row["todoist_id"],))
                _event(connection, row["todoist_id"], "completed", "todoist")
    store.set_state(connection, "last_sync", clock.now())


def add(connection, text, instruction):
    task = todoist.quick_add(text)
    with connection:
        return _upsert(connection, task, _project_names(connection), "adjutant", instruction)


def complete(connection, row, instruction):
    todoist.close(row["todoist_id"])
    with connection:
        connection.execute("UPDATE tasks SET status = 'done' WHERE todoist_id = ?", (row["todoist_id"],))
        _event(connection, row["todoist_id"], "completed", "adjutant", instruction=instruction)


def reopen(connection, row, instruction):
    todoist.reopen(row["todoist_id"])
    task = todoist.get(row["todoist_id"])
    with connection:  # the row is still 'done' locally, so _upsert records the reopening
        return _upsert(connection, task, _project_names(connection), "adjutant", instruction)


def reschedule(connection, row, when, instruction):
    """Todoist parses the date ("Monday", "next Friday 9am", "in 3 days")."""
    task = todoist.update(row["todoist_id"], due_string=when)
    with connection:
        return _upsert(connection, task, _project_names(connection), "adjutant", instruction)


def by_num(connection, num):
    return connection.execute("SELECT * FROM tasks WHERE num = ?", (int(num),)).fetchone()


def find(connection, reference, status="open"):
    """A task by number ('12', '#12') or by a title fragment that matches exactly one task."""
    reference = reference.strip()
    if reference.lstrip("#").isdigit():
        row = by_num(connection, reference.lstrip("#"))
        if row is None:
            raise NoMatch(reference)
        return row
    rows = connection.execute("SELECT * FROM tasks WHERE status = ? AND content LIKE ? ORDER BY num",
                              (status, f"%{reference}%")).fetchall()
    if not rows:
        raise NoMatch(reference)
    if len(rows) > 1:
        raise Ambiguous(rows)
    return rows[0]


def open_tasks(connection):
    return connection.execute(
        "SELECT * FROM tasks WHERE status = 'open' ORDER BY due_date IS NULL, due_date, priority DESC, num").fetchall()


def due(connection, comparison):
    """comparison: '<' for overdue, '=' for due today."""
    return connection.execute(
        f"SELECT * FROM tasks WHERE status = 'open' AND due_date {comparison} ? ORDER BY due_date, priority DESC, num",
        (clock.today().isoformat(),)).fetchall()


def history(connection, row):
    return connection.execute("SELECT * FROM task_events WHERE todoist_id = ? ORDER BY id",
                              (row["todoist_id"],)).fetchall()


def completed_since(connection, since_iso):
    return connection.execute(
        "SELECT t.*, e.time AS done_at, e.source FROM task_events e JOIN tasks t USING (todoist_id) "
        "WHERE e.event = 'completed' AND e.time >= ? ORDER BY e.time", (since_iso,)).fetchall()


def ref(row, width=40):
    """'#12 (Send Dana the FAQ)': a number always travels with its title."""
    title = row["content"] if len(row["content"]) <= width else row["content"][:width - 1] + "…"
    return f"#{row['num']} ({title})"


def line(row):
    extra = []
    if row["due_date"]:
        extra.append(clock.describe_day(row["due_date"]))
    if row["priority"] and row["priority"] > 1:
        extra.append(f"p{5 - row['priority']}")
    if row["project"] and row["project"] != "Inbox":
        extra.append(f"#{row['project']}")
    return f"#{row['num']:<4} {row['content']}" + (f"  — {' · '.join(extra)}" if extra else "")
