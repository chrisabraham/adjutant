# The patterns

Ten ideas from a year of building a personal assistant that gets used every day. Each one has a module, a test, and a reason. Take any of them on its own.

## 1. An outside authority plus a local append-only history

**Where:** `adjutant/ledger.py` · **Tests:** `Tasks`

Don't build a task manager. Use a real one (Todoist) as the authority on what's open, and keep your own permanent log beside it. Each sync compares Todoist with the local copy and writes an event for every difference, including changes made in the Todoist app. Events are only ever inserted.

You get three things a chat assistant can't give you:
- **Short numbers that never change.** `#12` is the same task forever, so `adj 12 done` is safe to type from memory.
- **History Todoist doesn't keep.** "Where did this task come from?" and "what did I finish last week?" still work after Todoist has archived the task.
- **Honest failure.** When Todoist is down, reads show the saved copy with its age, and writes refuse.

**Without it:** an assistant that "remembers" your tasks in a chat transcript, and quietly disagrees with your real list.

## 2. Deterministic plain English first

**Where:** `adjutant/router.py`, `tests/phrases.tsv` · **Tests:** `Replay`, `Tasks`

The fifty things you say every day are regular expressions, checked before any model is called. They're instant, free, identical every time, and testable. The model handles only what's left.

Three details matter more than they look:
- **Accept the short form.** People cut commands down: `push 12 Monday`, `done12`, `12 13 done`. If the short form falls through to the model, it costs money, takes seconds, and needs a "yes". The fix is a regex, not a prompt.
- **Misfires get help, not the model.** A short line shaped like a command (`move push 12 Monday`) that matches nothing gets "that isn't a command" and the right forms. It never goes to the model, which would cheerfully guess.
- **Compound input is refused.** `push 12 Monday; done 13` stops with nothing changed, so a date parser never reads "Monday; done 13" as a date.

`tests/phrases.tsv` records how you actually talk to it, and each line says where it must land. When something you typed went to the model and shouldn't have, add the line first, then fix the router.

## 3. Minutes as data

**Where:** `adjutant/minutes.py` · **Tests:** `Minutes`

"I decided…", "I owe Dana…", "Sam owes me…", "note: …" are recorded from the first sentence, with no model call. Each minute has a kind, so you can ask "what did I promise?" or "what am I waiting on?" and get a list instead of a summary.

Nothing is deleted:
- A **correction** is a new entry that supersedes the old one.
- **"Scratch that"** marks an entry struck. It drops out of reports and stays in the record.
- **Resolved** closes an open promise or wait.

A record you can edit is a record you can't trust.

## 4. Briefs: packet, one call, stored

**Where:** `adjutant/briefs.py` · **Tests:** `Models`

The brief is built in two halves. Code gathers the facts (overdue, due today, minutes, open promises, last night's close) into a plain-text packet. One model call turns the packet into prose under strict rules: use only the record, give every task number with its title, say each thing once, label suggestions. Both halves are stored.

Because the packet is code, you can test it, read it, and diff it when a brief seems wrong. Because there's one call, the cost is fixed. With no model, the packet is printed as-is, and it's already a usable brief.

## 5. What am I forgetting

**Where:** `adjutant/forgetting.py` · **Tests:** `Forgetting`

Slipping is detectable without a model: overdue for two weeks, pushed three times, a promise three days old, a wait five days old. Each finding has a stable key, so a snooze hides exactly that finding until a date, with the reason stored beside it. When the date passes, it comes back on its own.

## 6. Outside actions only on a human yes

**Where:** `router.offer`, `RUNNABLE` · **Tests:** `Offers`

The model may suggest commands. They're offered, never run: "Say yes and I'll run it." Only everyday, reversible, local commands can be offered at all (add, done, push, reopen), so a confused or manipulated answer can't produce anything worse. An offer lasts until your next request, and when it lapses you're told. A "yes" never goes missing in silence.

The original goes further: it never sends email. It writes drafts and you send them from your normal mail client, which is the send button you already trust.

## 7. A model per job, with fallbacks and a cost ledger

**Where:** `adjutant/model.py` · **Tests:** `Models`

Different jobs need different models: briefs need judgment, extraction needs speed. Each job has its own model and effort level, changeable with one command. Safety-classifier refusals fall back automatically to the model the API recommends. Every call records tokens and an estimated cost, so `adj spend` answers "what is this costing me?" from data, not a guess.

## 8. Tests that run the real CLI

**Where:** `tests/fakes.py`

Every test runs the actual `adj` command in a new throwaway home folder, against an in-process fake of Todoist and of the Anthropic API. Nothing touches the network or your real settings, and nothing is mocked inside the program. If the command works in the test, it works for you.

## 9. An encrypted backup with a tested restore

**Where:** `tools/backup.sh` · **Tests:** `Backup`

A consistent SQLite copy, encrypted with gpg, then decrypted again and integrity-checked, every time. A backup that has never been restored is a hope, not a backup. Optionally it's pushed to a private git repo, encrypted before it leaves.

## 10. Secrets and data that cannot reach git

**Where:** `.gitignore`, `adj init`, `tools/release_check.py` · **Tests:** `ReleaseCheck`

Secrets live in mode-600 files outside the repo, typed in with hidden input, never in environment files that get committed. The release check refuses to pass if it finds API keys, private keys, home paths, IP addresses or stray email addresses, or anything on your private denylist (client names, server names), which is kept outside the repo. Adjutant itself shipped only after passing the check against its author's own denylist.
