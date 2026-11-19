# The Upwork pattern

How the patterns in this repo run a freelance pipeline on Upwork. Written from daily practice. No tooling is assumed beyond a task list, a memory you trust, and a way to read your Upwork rooms—the author's desk reads them through the official API; a browser and a routine work too.

Upwork is an RFP channel, not a storefront. Buyers arrive with a problem and a deadline, most freelancers answer late or not at all, and the work goes to whoever ran the most disciplined desk. The pattern below is that desk.

## 1. Watch on a schedule, not on a whim

Rooms and invitations are checked on a cadence—replies often, new invitations a few times a day—and anything person-shaped surfaces the same day, in the morning brief, next to the day's tasks. A prospect's message that sits overnight because two narrower watchers each assumed the other had it is the founding failure this pattern exists to prevent.

## 2. Triage the same day

Every invitation gets a same-day answer or a same-day decline. When a contract is accepted, the work becomes tasks that day, and every task title carries the client's name and the money context—rate, cap, hours—so the board reads as revenue, not chores. A new engagement you have to be reminded of is already slipping.

## 3. Pitch inside the guardrails

Upwork's rules are the pitch's rules, enforced by the workflow rather than by memory:

- Before a contract exists: no email addresses, no phone numbers, no personal or company site links, no Calendly, Zoom, Meet, WhatsApp or LinkedIn links, and no wording that solicits contact ("book a time with me," "send me your email"). One helpful email address can get an account restricted.
- A screening question asking for your website is answered by pointing to the Upwork profile and portfolio.
- Every send is verified by reading the room back. A send receipt is a claim; the room is the record.

## 4. The concierge window

A new client's first days decide the engagement. While any client-side deliverable is outstanding—access, files, an answer—the client gets one touch per day: short, varied, each one shrinking the ask or adding value, never an identical nag. The cadence runs until they answer or the thread is formally closed or paused. A client who goes silent past a date they promised is escalated the same day, not discovered at day five.

## 5. Promises are minutes

Anything you say you will do—in a room, on a call, in a message—becomes a tracked commitment the day you say it. Saying it is not doing it: a commitment is discharged by verification (the delivered file, the live page, the read-back), never by the memory of having sent something. This is `adjutant/minutes.py` doing pipeline work.

## 6. Close every thread formally

Threads end won, lost, or parked with a reason—never abandoned in a tab. Parked work is marked complete rather than deleted: the record of what was offered, promised and decided is the asset, and it is what the forgetting audit reads when it asks what is slipping.

## Not auto-apply

Tools exist that point an agent at the API and spray proposals at every matching job. That is a volume game, and buyers can smell it. This pattern competes on the opposite axis: fewer pitches, each one inside the rules, and a follow-up discipline that treats a client's silence as a tracked state rather than a lost cause. If your advantage is judgment, automate the remembering, never the sending.

## What Adjutant does and does not do here

The core in this repo implements the discipline underneath: tasks with permanent numbers, minutes that supersede instead of deleting, briefs that gather before they write, and an audit that names what you are forgetting. The Upwork watch is an optional module: it lives in its own package, the core never imports it, and the core's promise—it never sends anything—stays true whether or not the module is installed. This document is the pattern the module follows, so you can also run it by hand and hold any wiring of your own to the same rules.
