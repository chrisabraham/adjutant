# Adjutant

Adjutant is the public, de-personalized spin-off of **Blackbox**, a command-line chief of staff: plain-English briefs, minutes, reminders, and follow-through for people whose memory doesn't hold on to things. Read it, borrow it, steal it. MIT, as is.

## What this is

Blackbox is a private command-line secretary built with Claude Code, running on a small server its author SSHes into. He talks to it in plain English: it runs his morning brief, watches unread mail, keeps his task list honest, drafts, remembers, and follows up. Adjutant is that machine with the man taken out of it — the same engine and patterns, with names, clients, data, prompts, and server details removed, published so anyone can read the code and take what's useful.

Even the name is borrowed: one of the chatbots coined "Adjutant" and the author adopted it on sight.

## Status: release in progress

This release began on **October 18, 2026**, ahead of the original schedule. This repository is the stake in the ground. The engine itself lands here as a clean export with fresh history — never as the private repository flipped public — after a scrub pass, and nothing ships unless the release check passes: it refuses to publish if it finds client names, personal paths, or secrets.

Adjutant is show-and-tell, an example rather than a product. No roadmap, no support promises.

## The patterns

What Blackbox does, written so it can be taken apart:

1. An outside authority (a real task service) plus a local append-only history.
2. Deterministic plain English first, tested by replaying your own message history.
3. Minutes as data, with supersede and strike instead of delete.
4. Briefs: gather a packet, make one model call, store the result.
5. "What am I forgetting," with snoozes that remember why.
6. Outside actions only on a human yes, with the normal mail client as the send button.
7. A model per job, with fallbacks and a cost ledger.
8. Tests that run the real CLI against fakes in a throwaway home folder.
9. An encrypted nightly backup with a tested restore.
10. Secrets and data that cannot reach git.

## More

- The project page: https://chrisabraham.net/projects.html#adjutant
- The wiki entry: https://chrisabraham.net/wiki/adjutant.html
- The private original, described: https://chrisabraham.net/wiki/blackbox.html

## License

MIT. See [LICENSE](LICENSE).
