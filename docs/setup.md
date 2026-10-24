# Setup

About ten minutes. You need Python 3.10 or newer and a Todoist account (the free plan works).

## 1. Install

```sh
pipx install git+https://github.com/chrisabraham/adjutant.git
```

No pipx? `python3 -m pip install --user git+https://github.com/chrisabraham/adjutant.git` works too. To hack on it, clone the repo and run `python3 -m adjutant` from the checkout.

## 2. Connect Todoist

In Todoist, go to **Settings → Integrations → Developer** and copy your API token. Then run:

```sh
adj init
```

Paste the token when it asks. Input is hidden, and the token lands in `~/.config/adjutant/todoist-token` with mode 600. `init` then syncs, and each of your open tasks gets its short number.

```sh
adj today
adj tasks
```

## 3. Optional: a model, for briefs and questions

Everything in the tasks, minutes and "what am I forgetting" sections works without a model. Briefs fall back to printing the record they would have used, and questions say plainly that no model is set up.

To turn the model on:

```sh
pipx inject adjutant-cli anthropic      # or: pip install --user anthropic
adj init                                 # paste an Anthropic API key when asked
adj models
```

Each job has its own model and effort level. Change one with `adj use sonnet for chat`, or all of them with `adj use haiku for everything`. Every call is recorded with its token counts and an estimated cost: `adj spend`. The prices in `adjutant/model.py` are a snapshot, so check current pricing before you rely on them.

## 4. Optional: people, from oversoul

If you keep an [oversoul](https://github.com/chrisabraham/oversoul) repo (one Markdown profile per person, shared by all your AI agents), point Adjutant at your copy:

```sh
echo ~/code/my-oversoul > ~/.config/adjutant/people-dir
adj who is Dana
```

Adjutant only reads it.

## 5. Optional: run it on a small server

Its author runs the original on a small cloud server and reaches it from every laptop over SSH. One database means one history, whichever laptop you're on.

On the server:

```sh
pipx install git+https://github.com/chrisabraham/adjutant.git
adj init
```

On each laptop, a two-line launcher saved as `~/bin/adj`:

```sh
#!/usr/bin/env bash
exec ssh -o LogLevel=ERROR -t myserver "~/.local/bin/adj $(printf ' %q' "$@")"
```

`LogLevel=ERROR` hides ssh's "Connection closed" line but keeps real errors.

## 6. Nightly encrypted backup

```sh
umask 077; head -c 32 /dev/urandom | base64 > ~/.config/adjutant/backup-passphrase
```

Put a copy of that passphrase in your password manager. Then run the script once by hand. It makes a backup and proves it restores:

```sh
tools/backup.sh
```

For an off-machine copy, clone a **private** git repo and set `ADJUTANT_BACKUP_REPO` to it. The file is encrypted before it leaves. To run it nightly, see `systemd/` or use cron:

```
30 3 * * *  ADJUTANT_BACKUP_REPO=$HOME/adjutant-backup $HOME/adjutant/tools/backup.sh >> $HOME/.local/share/adjutant/backup.log 2>&1
```

## 7. Optional: the morning brief, waiting for you

`systemd/` has a user timer that runs `adj good morning` at 7:00 and stores the result. Read it later with `adj good morning` (it makes a fresh one) or from the `briefs` table.

## Settings

| File in `~/.config/adjutant/` | What |
|---|---|
| `todoist-token` | Todoist API token (required) |
| `anthropic-api-key` | Anthropic API key (optional) |
| `models.json` | per-job model overrides (written by `adj use …`) |
| `people-dir` | path to your oversoul copy (optional) |
| `backup-passphrase` | backup encryption passphrase (optional) |
| `release-denylist.txt` | private words `tools/release_check.py` must never find (for forks) |

| Environment | What |
|---|---|
| `ADJUTANT_TIMEZONE` | your zone, e.g. `Europe/Berlin` (default `America/New_York`) |
| `ADJUTANT_NOW` | pin the clock (tests, replays) |
| `ADJUTANT_TODOIST_URL`, `ADJUTANT_ANTHROPIC_URL` | point at fakes (tests) |
| `XDG_CONFIG_HOME`, `XDG_DATA_HOME` | move the settings and data folders |
