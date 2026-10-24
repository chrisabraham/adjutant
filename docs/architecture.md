# Architecture

```
adj <words>  ──►  cli.main  ──►  router.handle
                                    │
        compound input? ── refuse   │
        "yes"? ── run the waiting offer (each command back through handle)
                                    │
        reads   (today, overdue, history…)   ── ledger.sync, then ledger queries
        writes  (done, push, add, reopen)    ── ledger.sync (must succeed), then todoist + task_events
        local   (minutes, briefs, forgetting, people, models)
        "X is done"                          ── complete the one matching task, else a done minute
        minutes.capture                       ── "I decided / I owe / … owes me / note:"
        misfire                               ── command-shaped but unmatched: help, no model
        chat                                  ── model.call("chat"), suggestions become an offer
```

## Modules

| Module | Job | Talks to |
|---|---|---|
| `cli.py` | `adj`, `adj init`, `adj status`, the interactive session | router, store |
| `router.py` | plain English → action; offers; chat | everything below |
| `ledger.py` | local task mirror with stable numbers and an event log | todoist, SQLite |
| `todoist.py` | Todoist API v1, standard library only | the network |
| `minutes.py` | capture and query the day's record | SQLite |
| `briefs.py` | packet → one model call → stored brief | ledger, minutes, model |
| `forgetting.py` | slipping checks and snoozes | ledger, minutes |
| `people.py` | read-only lookups in an oversoul folder | the filesystem |
| `model.py` | per-job model routing, fallbacks, cost ledger | Anthropic SDK (optional) |
| `store.py` | paths, the database, small state, the transcript | SQLite |
| `clock.py` | local time, pinnable for tests | |

## Tables

| Table | Rows are… | Ever updated? |
|---|---|---|
| `tasks` | the latest known state of each task, with its short number | yes (it's a mirror) |
| `task_events` | every change to every task, from either side | never |
| `minutes` | each minute; status moves active → resolved / superseded / struck | status only |
| `briefs` | each brief's packet and text | never |
| `usage` | each model call's tokens and cost | never |
| `snoozes` | a finding hidden until a date, with the reason | replaced on re-snooze |
| `transcript` | every request and reply | never |
| `state` | small keys: last sync, the waiting offer, last findings | yes |

## Decisions

- **Standard library only for the core.** The Anthropic SDK is the one optional dependency. A tool you rely on daily shouldn't break when a dependency does.
- **SQLite, one file.** Easy to back up, query, and copy between machines.
- **Todoist's own date parser.** `push 12 next Friday 9am` is passed to Todoist as a `due_string`. There's no date parsing here to get wrong.
- **Numbers travel with titles.** Everything the program prints about a task says `#12 (Send Dana the FAQ)`, never a bare `#12`.
- **The model never sees secrets, and never decides state.** It reads a packet and writes text. State changes come only from fixed commands.
