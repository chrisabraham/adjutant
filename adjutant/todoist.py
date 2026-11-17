"""A minimal Todoist API v1 client, standard library only.

The token is read from ~/.config/adjutant/todoist-token and leaves this module only in
the Authorization header. ADJUTANT_TODOIST_URL points it at a fake for tests.
"""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

from . import store


class TodoistError(Exception):
    pass


class NotConfigured(TodoistError):
    pass


def base_url():
    return os.environ.get("ADJUTANT_TODOIST_URL", "https://api.todoist.com/api/v1").rstrip("/")


def configured():
    return bool(store.secret("todoist-token"))


RATE_RETRIES = 3        # Todoist's "too many requests": wait what it asks, then try again, this many times
MAX_WAIT_SECONDS = 60   # a longer requested wait is reported instead of slept through


def _retry_after(error, detail):
    """Seconds Todoist asked us to wait: its Retry-After header, else error_extra.retry_after, else 5."""
    for value in (error.headers.get("Retry-After") if error.headers else None,
                  ((json.loads(detail) if detail.startswith("{") else {}).get("error_extra") or {}).get("retry_after")):
        try:
            if value is not None:
                return max(0.0, float(value))
        except (TypeError, ValueError):
            continue
    return 5.0


def _request(method, path, params=None, body=None):
    token = store.secret("todoist-token")
    if not token:
        raise NotConfigured("Todoist isn't connected: put your API token in ~/.config/adjutant/todoist-token")
    url = base_url() + path + ("?" + urllib.parse.urlencode(params) if params else "")
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if method == "POST":
        # Lets Todoist drop a duplicate if a retry repeats this exact write.
        headers["X-Request-Id"] = str(uuid.uuid4())
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    # Pace to what the service says (lesson: "Ask the service how fast"). A 429 is retried after the wait
    # Todoist names, with the same X-Request-Id, so a write that did land is never applied twice.
    for attempt in range(RATE_RETRIES + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
            return json.loads(raw) if raw else None
        except urllib.error.HTTPError as error:
            if error.code in (401, 403):
                raise TodoistError(f"Todoist refused the token (HTTP {error.code}).") from None
            detail = error.read().decode("utf-8", errors="replace")[:300]
            if error.code == 429:
                wait = _retry_after(error, detail)
                if attempt < RATE_RETRIES and wait <= MAX_WAIT_SECONDS:
                    time.sleep(wait)
                    continue
                raise TodoistError(f"Todoist says too many requests; it asked for a {wait:g}-second pause. "
                                   "Try again in a minute.") from None
            raise TodoistError(f"Todoist HTTP {error.code}: {detail}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            raise TodoistError(f"Couldn't reach Todoist: {error}") from None


def _paged(path, key, params=None):
    params = dict(params or {}, limit=200)
    results = []
    while True:
        page = _request("GET", path, params)
        results.extend(page.get(key) or [])
        if not page.get("next_cursor"):
            return results
        params["cursor"] = page["next_cursor"]


def active_tasks():
    return _paged("/tasks", "results")


def projects():
    return _paged("/projects", "results")


def completed_between(since, until):
    return _paged("/tasks/completed/by_completion_date", "items", {"since": since, "until": until})


def quick_add(text):
    """Todoist's own parser handles dates, #Project, @label and p1."""
    return _request("POST", "/tasks/quick", body={"text": text})


def update(task_id, **fields):
    return _request("POST", f"/tasks/{urllib.parse.quote(task_id)}", body=fields)


def close(task_id):
    _request("POST", f"/tasks/{urllib.parse.quote(task_id)}/close")


def reopen(task_id):
    _request("POST", f"/tasks/{urllib.parse.quote(task_id)}/reopen")


def get(task_id):
    return _request("GET", f"/tasks/{urllib.parse.quote(task_id)}")
