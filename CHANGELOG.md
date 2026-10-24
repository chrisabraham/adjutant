# Changelog

## 0.1.0 (2026-10-24)

First release: a clean rewrite of the Blackbox engine, with no personal data.

- Todoist tasks with short permanent numbers and a local, append-only change history (`ledger`)
- A deterministic plain-English router, with short forms (`push 12 Monday`, `done12`, `12 13 done`), misfire help, a compound-input refusal, and a replay test of recorded phrasings
- Minutes from plain sentences, with supersede, strike and resolve
- Morning, night and weekly briefs: packet, one model call, stored; the packet is printed when no model is set up
- "What am I forgetting" with snoozes that keep their reason
- Model suggestions offered, never run, and announced when they lapse
- Per-job model routes and effort, refusal fallback, and a cost ledger
- `adj who is` reads an oversoul people folder
- `adj init` guided setup; `adj status`
- Encrypted backup with a restore test every run; release check with a private denylist
- 40 tests that run the real CLI against in-process fakes
