# Lessons

What went wrong in daily use of the private original, and the rule each mistake produced. Newest first.

**A refusal shaped like an answer is still a refusal.**
A batch job fetched a hundred postings from an outside service, then asked a model to judge each one. The service started saying "you're opening these too quickly, slow down", but it said so in a normal-looking reply, not as an error. The code read each refusal as an empty posting, paid the model to judge seventy blanks, and saved seventy confident-sounding verdicts about nothing. Since they were saved, nothing would ever look at those postings again. *Rule: recognise error-shaped replies where they enter the program, and raise. Never send an empty input to a model. Something you couldn't fetch is "not fetched", saved as nothing, so the next run tries again. Fetch at a polite pace, and stop when told to slow down.*

**Out of credit, ninety-nine times.**
The model account ran dry partway through a batch. Every remaining item made its own call, got the same billing error, and printed the same block of JSON: ninety-nine screens of one fact. The error was also filed as a rate limit, which suggested waiting would help. It wouldn't. *Rule: an error no retry can fix (no credit, a revoked key) ends the batch and is said once, in plain words, with the fix. A real rate limit gets a pause and a retry.*

**The schema said text; the model sent a number.**
A structured reply promised a rate as a string, and one day the model sent `25`. A regular expression downstream crashed on it, two commands later, far from the cause. *Rule: a schema is a request, not a guarantee. Normalise the model's output types where it enters the program.*

**Put what to act on where the scroll stops.**
A long run printed a hundred verdicts, newest first, and the dozen worth acting on were scattered through them. On a busy day the user had to hunt. *Rule: keep the full record, but repeat the actionable items, compactly, as the last thing printed. Offer a short command that prints only those.*

**The clock goes last.**
A prompt started with the current time. Everything after it was the same on every call, but because the first line changed every minute, the provider's prompt cache never matched, and every call paid full price for thousands of identical tokens. *Rule: unchanging instructions first, per-call facts (the time, the item) last.* `model.call` sends the stable system prompt marked cacheable for this reason.

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
