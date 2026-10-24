"""Where things live, and the one SQLite database.

Settings and secrets:  ~/.config/adjutant/       (mode 700, never in git)
Data:                  ~/.local/share/adjutant/  (the database, backups)

Both follow XDG_CONFIG_HOME / XDG_DATA_HOME when set.
"""

import json
import os
import sqlite3
from pathlib import Path


def config_dir():
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "adjutant"


def data_dir():
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "adjutant"


def secret(name):
    """Read a one-line secret file from the config folder, or '' if it isn't there."""
    try:
        return (config_dir() / name).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


SCHEMA = """
CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS transcript (
    id INTEGER PRIMARY KEY,
    time TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    text TEXT NOT NULL
);
"""


def connect():
    folder = data_dir()
    folder.mkdir(parents=True, exist_ok=True)
    folder.chmod(0o700)
    connection = sqlite3.connect(folder / "adjutant.sqlite3")
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    from . import ledger, minutes, model, briefs, forgetting
    for module in (ledger, minutes, model, briefs, forgetting):
        connection.executescript(module.SCHEMA)
    connection.commit()
    return connection


def get_state(connection, key, default=None):
    row = connection.execute("SELECT value FROM state WHERE key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else default


def set_state(connection, key, value):
    with connection:
        connection.execute("INSERT INTO state(key, value) VALUES (?, ?) "
                           "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, json.dumps(value)))


def take_state(connection, key):
    value = get_state(connection, key)
    with connection:
        connection.execute("DELETE FROM state WHERE key = ?", (key,))
    return value


def log(connection, role, text):
    """The permanent transcript: every request and reply, append-only."""
    from . import clock
    with connection:
        connection.execute("INSERT INTO transcript(time, role, text) VALUES (?, ?, ?)", (clock.now(), role, text))
