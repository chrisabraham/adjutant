"""The adj command: one-shot (adj 12 done), an interactive session (adj), and setup (adj init)."""

import getpass
import os
import re
import select
import sys

from . import __version__, ledger, model, people, router, store, todoist

INTERACTIVE_HELP = "Type a request, 'help' for the commands, 'exit' to leave."


def _write_secret(name, value):
    folder = store.config_dir()
    folder.mkdir(parents=True, exist_ok=True)
    folder.chmod(0o700)
    path = folder / name
    path.write_text(value.strip() + "\n", encoding="utf-8")
    path.chmod(0o600)


def init():
    """Guided setup. Secrets are typed without echo and land in mode-600 files, never in git."""
    print(f"Adjutant {__version__} setup. Settings go in {store.config_dir()} (mode 700).\n")
    if not todoist.configured() or input("Todoist is already connected. Replace the token? [y/N] ").lower() == "y":
        print("Todoist: Settings → Integrations → Developer → API token.")
        token = getpass.getpass("Paste the Todoist API token (input is hidden): ").strip()
        if token:
            _write_secret("todoist-token", token)
    connection = store.connect()
    try:
        ledger.sync(connection)
        print(f"Todoist connected: {len(ledger.open_tasks(connection))} open tasks, each now has a short number.")
    except todoist.TodoistError as error:
        print(f"Todoist check failed: {error}")

    if not store.secret("anthropic-api-key"):
        print("\nOptional: an Anthropic API key for briefs and questions (everything else works without one).")
        key = getpass.getpass("Paste the key, or press Enter to skip (input is hidden): ").strip()
        if key:
            _write_secret("anthropic-api-key", key)
    if model.available():
        print("Model calls: on. See them with: adj models")
    elif store.secret("anthropic-api-key"):
        print("Model calls: the key is saved, but the SDK is missing: pip install anthropic")

    if not people.folder():
        print("\nOptional: the folder of an oversoul copy, for 'adj who is Dana' (https://github.com/chrisabraham/oversoul).")
        folder = input("Path, or Enter to skip: ").strip()
        if folder:
            _write_secret("people-dir", os.path.expanduser(folder))
    print("\nDone. Try: adj today · adj good morning · adj help")


def status(connection):
    sync = store.get_state(connection, "last_sync")
    tasks = connection.execute("SELECT COUNT(*) FROM tasks WHERE status = 'open'").fetchone()[0]
    spent = connection.execute("SELECT COALESCE(SUM(cost), 0) FROM usage").fetchone()[0]
    print(f"Adjutant {__version__}")
    print(f"Todoist:  {'connected' if todoist.configured() else 'not connected (adj init)'}; "
          f"{tasks} open tasks; last sync {sync or 'never'}")
    print(f"Model:    {'on' if model.available() else 'off (optional)'}; estimated spend ${spent:.4f}")
    print(f"People:   {people.folder() or 'no oversoul folder set (optional)'}")
    print(f"Data:     {store.data_dir()}")


def session(connection):
    print(f"Adjutant {__version__}. {INTERACTIVE_HELP}")
    while True:
        try:
            line = input("adj> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line.strip().lower() in ("exit", "quit", "bye"):
            return
        # A paste arrives all at once: gather it. A list of "adj ..." lines runs line by line.
        lines = [line]
        while sys.stdin.isatty() and select.select([sys.stdin], [], [], 0.2)[0]:
            more = sys.stdin.readline()
            if not more:
                break
            lines.append(more.rstrip("\n"))
        lines = [l for l in lines if l.strip()]
        if len(lines) > 1 and all(re.match(r"\s*adj\s+\S", l) for l in lines):
            for request in lines:
                print(f"> {request.strip()}")
                router.handle(connection, re.sub(r"^\s*adj\s+", "", request))
        else:
            router.handle(connection, re.sub(r"^\s*adj\s+", "", "\n".join(lines)))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] in (["--version"], ["version"]):
        print(__version__)
        return 0
    if argv[:1] == ["init"]:
        init()
        return 0
    connection = store.connect()
    if argv[:1] == ["status"]:
        status(connection)
    elif argv:
        router.handle(connection, " ".join(argv))
    else:
        session(connection)
    return 0
