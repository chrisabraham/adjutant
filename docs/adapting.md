# Adapting it

Adjutant ships about 80% finished on purpose. The last 20% is yours.

## Teach it how you talk

1. Use it for a week. Each time something you typed went to the model, or got "isn't a command", write the line down.
2. Add each line to `tests/phrases.tsv` with the route it should take (`fixed` or `chat`).
3. Run `python3 -m unittest discover -s tests`. The replay test fails and lists the lines.
4. Add or widen a pattern in `router.handle` until it passes.

That loop is the whole method behind the original's router.

## Add a command

Pick the list it belongs in:
- `reads`: it shows tasks, so it syncs first and falls back to the saved copy.
- `writes`: it changes Todoist, so it refuses if Todoist is unreachable.
- `local`: it needs neither.

Write the pattern as a full match on the lower-cased request, then add a test in `tests/test_adjutant.py` that runs the real command.

## Swap the task service

`todoist.py` is about a hundred lines. Keep the function names (`active_tasks`, `quick_add`, `update`, `close`, `reopen`, `get`, `projects`) and the shape `ledger.py` expects (`id`, `content`, `priority`, `labels`, `project_id`, `due.date`, `due.string`), and the rest works unchanged.

## Swap the model

`model.call(connection, job, system, messages)` is the only entry point. Replace its body with any provider and keep the usage row.

## Add a brief section

Add a section to `briefs.packet` (code, testable), then mention it in the ask for that brief. Keep the rule that the model uses only the record.

## Ideas the original has that this doesn't (yet)

- Google Calendar in the morning brief, with focus blocks between meetings
- Unread mail from real people (not newsletters) in the brief, with links
- Email drafts in your voice, sent from your normal mail client
- A job-board triage queue with verdicts
- Checkpoints: `checkpoint PROJECT :: where I stopped :: next step`, then `get me back into PROJECT`
- A diary paragraph appended to a dated text file at the end of each day

Each started as one sentence typed into the original that went to the model. That's how you find yours.
