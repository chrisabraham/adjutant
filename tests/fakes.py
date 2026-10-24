"""In-process fakes for Todoist and the Anthropic Messages API, and a harness that runs the real CLI.

Pattern 8. Tests run the real `adj` command in a throwaway home folder against these fakes.
Nothing touches the network, a real account, or your own settings.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parent.parent
NOW = "2026-09-30T10:00:00"  # a Wednesday
TODAY = date(2026, 9, 30)
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def parse_due(text):
    """Enough of Todoist's date parser for tests: today, tomorrow, weekdays, next weekday, ISO dates."""
    text = (text or "").strip().lower()
    if text == "today":
        return TODAY
    if text == "tomorrow":
        return TODAY + timedelta(days=1)
    words = text.split()
    if words and words[-1] in WEEKDAYS:
        ahead = (WEEKDAYS.index(words[-1]) - TODAY.weekday()) % 7 or 7
        return TODAY + timedelta(days=ahead + (7 if words[0] == "next" and ahead < 7 else 0))
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


class FakeServices:
    def __init__(self):
        self.tasks = {}
        self.projects = [{"id": "p1", "name": "Inbox"}, {"id": "p2", "name": "Work"}]
        self.next_id = 100
        self.reply = "A plain answer."
        self.chat_requests = []
        self.writes = []

    def task(self, content, due=None, priority=1, project="p1"):
        self.next_id += 1
        tid = str(self.next_id)
        self.tasks[tid] = {"id": tid, "content": content, "priority": priority, "project_id": project,
                           "labels": [], "due": {"date": due, "string": due} if due else None, "done": False}
        return tid

    def active(self):
        return [{k: v for k, v in t.items() if k != "done"} for t in self.tasks.values() if not t["done"]]


def make_handler(fake):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, payload, code=200):
            body = json.dumps(payload).encode() if payload is not None else b""
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self):
            length = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(length) or b"{}") if length else {}

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/tasks":
                return self._send({"results": fake.active(), "next_cursor": None})
            if path == "/projects":
                return self._send({"results": fake.projects, "next_cursor": None})
            if path == "/tasks/completed/by_completion_date":
                return self._send({"items": [], "next_cursor": None})
            if path.startswith("/tasks/"):
                task = fake.tasks.get(path.split("/")[2])
                return self._send({k: v for k, v in task.items() if k != "done"}) if task else self._send({}, 404)
            self._send({}, 404)

        def do_POST(self):
            path = urlparse(self.path).path
            body = self._body()
            if path.startswith("/v1/messages"):
                fake.chat_requests.append(body)
                return self._send({
                    "id": f"msg_{len(fake.chat_requests)}", "type": "message", "role": "assistant",
                    "model": body.get("model"), "content": [{"type": "text", "text": fake.reply}],
                    "stop_reason": "end_turn", "stop_sequence": None,
                    "usage": {"input_tokens": 1000, "output_tokens": 200}})
            fake.writes.append((path, body))
            if path == "/tasks/quick":
                tid = fake.task(body["text"])
                return self._send({k: v for k, v in fake.tasks[tid].items() if k != "done"})
            parts = path.strip("/").split("/")
            task = fake.tasks.get(parts[1]) if len(parts) > 1 else None
            if task is None:
                return self._send({"error": "not found"}, 404)
            if len(parts) == 3 and parts[2] == "close":
                task["done"] = True
                return self._send(None, 204)
            if len(parts) == 3 and parts[2] == "reopen":
                task["done"] = False
                return self._send(None, 204)
            if "due_string" in body:
                day = parse_due(body["due_string"])
                task["due"] = {"date": day.isoformat(), "string": body["due_string"]} if day else None
            if "content" in body:
                task["content"] = body["content"]
            return self._send({k: v for k, v in task.items() if k != "done"})
    return Handler


class CLITestCase(unittest.TestCase):
    """Each test gets fresh fakes and a fresh home folder, and runs the real CLI."""

    def setUp(self):
        self.fake = FakeServices()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.fake))
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.home = Path(tempfile.mkdtemp(prefix="adjutant-test-"))
        config = self.home / ".config" / "adjutant"
        config.mkdir(parents=True)
        (config / "todoist-token").write_text("fake-token\n")

    def tearDown(self):
        self.stop_services()
        shutil.rmtree(self.home)

    def stop_services(self):
        """Take the fakes offline (also used to test an unreachable Todoist)."""
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

    def with_model(self):
        try:
            import anthropic  # noqa: F401
        except ImportError:
            self.skipTest("the Anthropic SDK isn't installed")
        (self.home / ".config" / "adjutant" / "anthropic-api-key").write_text("fake-key\n")

    def adj(self, *words, stdin=None):
        env = {"HOME": str(self.home), "PATH": os.environ.get("PATH", ""), "ADJUTANT_NOW": NOW,
               "ADJUTANT_TODOIST_URL": self.url, "ADJUTANT_ANTHROPIC_URL": self.url,
               "PYTHONPATH": str(REPO), "LANG": "C.UTF-8"}
        result = subprocess.run([sys.executable, "-m", "adjutant", *words], input=stdin, env=env,
                                capture_output=True, text=True, timeout=60, cwd=self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout + result.stderr

    def db(self):
        import sqlite3
        connection = sqlite3.connect(self.home / ".local" / "share" / "adjutant" / "adjutant.sqlite3")
        connection.row_factory = sqlite3.Row
        return connection
