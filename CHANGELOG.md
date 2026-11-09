# Changelog

## Unreleased

- An out-of-credit model account now says so plainly ("out of credit … add credit, then try again") instead of "Anthropic error 400", and is never presented as a rate limit; the deterministic packet still prints
- Five new lessons from the private original: a refusal shaped like an answer, out of credit ninety-nine times, the schema said text but the model sent a number, put what to act on where the scroll stops, and the clock goes last
- The test fakes can answer model calls with an error (`fake.model_error`); 41 tests

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
