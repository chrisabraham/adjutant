# Lessons

What went wrong in daily use of the private original, and the rule each mistake produced. Newest first.

**Fresh donuts.**
The author's word for the newest postings is "fresh donuts". It comes from a night in Northern Virginia in the 1990s, when his friend Jean Amendolia drove him to a Krispy Kreme just as a new batch came off the line and the neon "Hot Now" sign switched on. He doesn't see pictures in his mind's eye, so what he kept is the story: the drive, the company, and being there when the light came on. Thanks, Jean. The phrase stuck: years later he was writing it for clients as SEO doctrine ("[Like I keep on saying, Google only wants hot donuts](https://biznology.com/2018/03/online-reputation-management-orm-dont-forget-google-when-youre-in-crisis-mode/)", March 2018). The private original applies that doctrine to his own work. On a job marketplace, the first credible reply often wins, so the private original's batch triage exists to show him the light as it comes on. For weeks it didn't: the list was grouped by verdict, so a posting from ten minutes ago sat below a strong one from yesterday, and the newest work was buried. He asked for fresh donuts for months before the order changed. *Rule: when freshness is the point, sort by freshness alone. The verdict is a label on each item, never its place in line. Show the age to the minute while it's under an hour.*

**A list shows only what you can still act on.**
A daily batch listed every fresh posting, and kept listing the ones the user had already answered. Each looked actionable, and each produced "you already did this one" when he tried it. The rule against hiding things was right; it was applied one step too far. *Rule: hide nothing the user might act on; leave out what's finished, and say in one line how many you left out.*

**The platform's form decides the shape.**
The model priced hourly jobs as flat fees, which read sensibly in a letter that the job's form couldn't accept: an hourly posting takes an hourly rate and nothing else. A prompt rule made it rarer, not rare. A bare number was worse, because "95" meant $95 an hour and the first fix read it as a flat fee. *Rule: check model output against what its destination accepts, in code. Ask once more at full strength, then flag; never silently convert. Read ambiguous values in the destination's terms, and when even that is ambiguous, ask.*

**Guard the outbound text, not just the prompt.**
A marketplace warned the user for sharing contact details before a contract. His drafts turned out to be clean, apart from one website link two weeks earlier, but a prompt instruction was the only thing that had kept them that way. *Rule: when a platform forbids something in what you send, strip it from the draft in code (addresses, phone numbers, outside links), list what was removed for a human to reread, and replay the guard over everything you've sent before to find what slipped through.*

**Ask the service how fast.**
A sweep of thirty-odd searches lost most of them every run. The reason was in the replies all along ("wait about 5 seconds; about 12 requests a minute"), but the code only saved "failed". Once it saved each failure's reason, the fix was obvious: a shared token bucket just under the stated rate, and a refusal pauses the whole bucket for the wait the service asks for. Every search succeeded, at the cost of a slower run, which the next lesson paid back. *Rule: save why each call failed, not just that it did. Pace to the rate the service states. A retry waits exactly as long as asked, and a retried write carries the same request id.* `todoist._request` does this for Todoist's 429.

**Don't fetch twice what one call can carry.**
A batch opened every item one call at a time after a search had already listed them, and the opening calls shared the same rate limit as the search. The search could return the full record all along; it had to be asked. A sweep under fifteen minutes old was also redone from scratch whenever a second command wanted it. *Rule: ask the list call for the full record and store it. Reuse a recent clean result, and say how old it is. Make "fetch again now" one short command.*

**A silent wait looks like a hang.**
A four-minute sweep printed nothing until it finished, and the user killed it twice. One of those runs was mid-retry after a network hiccup, which looked exactly like a freeze. *Rule: before any long wait, say what's happening, how long it usually takes, and that interrupting is safe; then count progress on one line. Write it to stderr, and only to a terminal, so pipes, logs and tests never see it.*

**Too many authors make rules that contradict.**
Several assistants and the user wrote rules into one shared playbook over a month. Older sections still said "pass" on things a newer ruling said to pursue, and the model read both in every prompt. One standing instruction even used a signal the user later called a red herring. *Rule: one voice for each rule. When a ruling changes, rewrite the old section to match and keep the old text in a dated backup, not beside the new text in the prompt.*

**Back up before you fix data.**
A script that corrected nineteen saved records had its own bug and knocked seven of them down to the wrong value. Since the database had been copied a minute before, they were restored exactly and corrected properly. *Rule: copy the data before any bulk correction, and read the corrected records before calling it done.*

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
