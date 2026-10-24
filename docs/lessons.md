# Lessons

What went wrong in daily use of the private original, and the rule each mistake produced. Newest first.

**The user types the short form, so the short form is the command.**
`push 12 Monday` without "to" fell through to the model, which correctly answered "push 12 to Monday" and then asked for a yes. Three tasks took six round trips and three model calls. The user had been dropping "to" on purpose, thinking terse meant canonical. *Rule: make the shortest natural form a fixed command; keep the long form as an alias. Teach the short form in every hint.*

**A "yes" must never vanish silently.**
An offer lasts until the next request. That's correct, because stale yeses are dangerous. But when four one-line commands were chained in the shell, each replaced the last offer, and a final "yes" would have run only one. *Rule: when an offer lapses unrun, say so in one line.*

**A paste is not one message.**
A list of commands pasted into the interactive session arrived as one request, went to the model as a paragraph, and the last line ran on its own. *Rule: a pasted block whose every line starts with the command name runs line by line; anything else is one message.*

**Noise teaches people to stop reading.**
"Indexed 2 transcript entries" printed on every run, and "Batch finished: 1 commands dispatched" followed a single command. Each was true and useless. *Rule: print only what the user would act on.*

**A model that suggests must never act.**
Chat answers often end with the right command. Running it automatically is one prompt injection away from disaster: email bodies and web pages reach the model as context. *Rule: suggestions become an offer; only reversible local commands can be offered; untrusted content is data, never instructions.*

**Tests that only test the parts lie.**
A mocked unit test can pass while the real command fails on a config path, an import, or an environment variable, and a daily tool fails at seven in the morning. *Rule: every test runs the real CLI in a throwaway home folder against fake services.*

**Scrubbing a personal tool leaks.**
The plan was to publish the private repo with names removed. A first pass found client names in test fixtures, real prices in examples, and a real client's first name used as a placeholder. *Rule: publish a clean rewrite, and gate every release on a check against a private denylist.*

**Briefs must sync first.**
A brief built from a stale local copy confidently reported "nothing overdue". *Rule: anything that reads tasks syncs first, and says so when it can't.*
