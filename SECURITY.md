# Security

## What Adjutant holds

- A Todoist API token and, optionally, an Anthropic API key, in `~/.config/adjutant/` (folder mode 700, files mode 600).
- A SQLite database of your tasks' history, your minutes, briefs and transcript in `~/.local/share/adjutant/`.

Nothing is sent anywhere except Todoist (task reads and writes you asked for) and, if configured, Anthropic (briefs and questions, with your task list and minutes as context).

## Guarantees the code keeps

- No secret is ever read from or written to the repository. `adj init` takes secrets with hidden input.
- The model cannot change state. Suggested commands run only on your "yes", and only reversible, local ones can be suggested.
- Backups are encrypted (gpg, AES-256) before they leave the machine, and every backup is restore-tested.
- `tools/release_check.py` blocks releases that contain keys, private keys, home paths, IP addresses, stray email addresses, or anything on a private denylist.

## Reporting a problem

Please don't open a public issue for a vulnerability. Use GitHub's private vulnerability reporting on this repository (Security → Report a vulnerability). There's no bounty and no SLA, but reports are read.
