"""Behaviour tests: the real CLI, fake services, a throwaway home folder."""

import json
import unittest

from fakes import CLITestCase


class Tasks(CLITestCase):
    def setUp(self):
        super().setUp()
        self.fake.task("Send Dana the FAQ", due="2026-09-29")
        self.fake.task("Call Sam", due="2026-09-30", priority=4)
        self.fake.task("Plan the offsite")

    def test_numbers_are_short_and_stable(self):
        out = self.adj("tasks")
        self.assertIn("#1    Send Dana the FAQ", out)
        self.fake.task("A newer task")
        self.adj("tasks")
        self.assertIn("#1    Send Dana the FAQ", self.adj("tasks"))
        self.assertIn("#4    A newer task", self.adj("tasks"))

    def test_today_shows_overdue_and_due(self):
        out = self.adj("today")
        self.assertIn("Send Dana the FAQ", out)
        self.assertIn("Call Sam", out)
        self.assertNotIn("Plan the offsite", out)
        self.assertIn("p1", out)

    def test_done_and_undo(self):
        self.adj("tasks")
        out = self.adj("1", "done")
        self.assertIn("Completed #1 (Send Dana the FAQ)", out)
        self.assertIn("Undo: adj reopen 1", out)
        self.assertIn("already done", self.adj("done", "1"))
        self.assertIn("Reopened #1", self.adj("reopen", "1"))

    def test_glued_and_several(self):
        self.adj("tasks")
        self.assertIn("Completed #1", self.adj("done1"))
        out = self.adj("2", "and", "3", "done")
        self.assertEqual(out.count("Completed #"), 2)

    def test_push_short_form_and_several(self):
        self.adj("tasks")
        self.assertIn("Moved #1 to Mon Oct 5", self.adj("push", "1", "Monday"))
        out = self.adj("push", "2", "3", "to", "Friday")
        self.assertEqual(out.count("Moved #"), 2)
        self.assertEqual(self.fake.chat_requests, [])

    def test_push_by_name(self):
        self.adj("tasks")
        self.assertIn("Moved #3", self.adj("push", "the", "offsite", "to", "Friday"))

    def test_ambiguous_name_changes_nothing(self):
        self.fake.task("Call Sam again")
        self.adj("tasks")
        out = self.adj("push", "Call Sam", "to", "Friday")
        self.assertIn("matches 2 tasks, so nothing changed", out)
        self.assertFalse([w for w in self.fake.writes if "due_string" in w[1]])

    def test_add_uses_quick_add(self):
        out = self.adj("add", "Email", "Lee", "Friday", "p2")
        self.assertIn("Added #4", out)
        self.assertEqual(self.fake.writes[0], ("/tasks/quick", {"text": "Email Lee Friday p2"}))

    def test_x_is_done_completes_the_matching_task(self):
        self.adj("tasks")
        self.assertIn("Completed #3 (Plan the offsite)", self.adj("the offsite is done"))

    def test_x_is_done_without_a_task_becomes_a_minute(self):
        self.assertIn("(done)", self.adj("the garage cleanup is done"))

    def test_history_includes_changes_made_in_todoist(self):
        self.adj("tasks")
        self.adj("push", "1", "Friday")
        self.fake.tasks["101"]["content"] = "Send Dana the revised FAQ"
        out = self.adj("history", "of", "1")
        self.assertIn("created", out)
        self.assertIn("via adjutant", out)
        self.assertIn("via todoist", out)
        self.assertIn("revised FAQ", out)

    def test_completed_in_the_todoist_app_is_recorded(self):
        self.adj("tasks")
        self.fake.tasks["102"]["done"] = True
        self.adj("tasks")
        self.assertIn("Call Sam", self.adj("what did I finish today"))

    def test_unreachable_todoist_shows_saved_copy_and_refuses_writes(self):
        self.adj("tasks")
        self.stop_services()
        self.assertIn("Showing the copy saved", self.adj("tasks"))
        self.assertIn("Not changing anything", self.adj("1", "done"))

    def test_compound_input_changes_nothing(self):
        self.adj("tasks")
        self.assertIn("several commands on one line", self.adj("push 1 Monday; done 2"))
        self.assertEqual(self.fake.writes, [])

    def test_broken_command_gets_help_not_the_model(self):
        self.with_model()
        out = self.adj("move", "push", "1", "Monday")
        self.assertIn("isn't a command", out)
        self.assertEqual(self.fake.chat_requests, [])


class Minutes(CLITestCase):
    def test_capture_kinds_without_a_model(self):
        self.assertIn("(decision)", self.adj("I decided to keep the price at $500"))
        self.assertIn("(waiting)", self.adj("Sam owes me the signed contract"))
        self.assertIn("(note)", self.adj("note: the venue holds 40"))
        out = self.adj("what happened today")
        self.assertIn("DECISIONS", out)
        self.assertIn("WAITING ON OTHERS", out)
        self.assertEqual(self.fake.chat_requests, [])

    def test_promise_offers_a_task(self):
        out = self.adj("I owe Dana the revised FAQ tomorrow")
        self.assertIn("(promise)", out)
        self.assertIn("Say yes", out)
        self.assertIn("Added #1", self.adj("yes"))
        self.assertIn("revised FAQ", self.adj("what do I owe Dana"))

    def test_correction_supersedes_and_keeps_the_original(self):
        self.adj("I decided to meet Tuesday")
        out = self.adj("correction: I decided to meet Wednesday")
        self.assertIn("m2 replaces m1", out)
        with self.db() as c:
            rows = c.execute("SELECT id, status, replaces FROM minutes ORDER BY id").fetchall()
        self.assertEqual([tuple(r) for r in rows], [(1, "superseded", None), (2, "active", 1)])

    def test_scratch_that_strikes_but_keeps(self):
        self.adj("idea: a podcast")
        self.assertIn("Struck m1", self.adj("scratch that"))
        self.assertNotIn("podcast", self.adj("what happened today"))
        with self.db() as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM minutes").fetchone()[0], 1)

    def test_resolve(self):
        self.adj("Sam owes me the contract")
        self.assertIn("Resolved m1", self.adj("m1", "resolved"))
        self.assertIn("Nothing open", self.adj("what am I waiting on"))


class Offers(CLITestCase):
    def setUp(self):
        super().setUp()
        self.fake.task("Old thing", due="2026-09-01")
        self.with_model()
        self.adj("tasks")

    def test_suggested_command_runs_only_on_yes(self):
        self.fake.reply = "Push it.\nadj push 1 Friday"
        out = self.adj("what should I do about the old thing?")
        self.assertIn("Say yes and I'll run it: adj push 1 Friday", out)
        self.assertFalse([w for w in self.fake.writes if "due_string" in w[1]])
        self.assertIn("Moved #1", self.adj("yes"))

    def test_unsafe_suggestions_are_never_offered(self):
        self.fake.reply = "adj use fable for everything\nadj delete everything"
        self.assertNotIn("Say yes", self.adj("anything else?"))

    def test_lapsed_offer_is_announced(self):
        self.fake.reply = "adj push 1 Friday"
        self.adj("what now?")
        out = self.adj("note: moving on")
        self.assertIn("lapsed; nothing from it ran", out)
        self.assertIn("nothing waiting", self.adj("yes"))

    def test_pick_some(self):
        self.fake.task("Second", due="2026-09-02")
        self.adj("tasks")
        self.fake.reply = "adj push 1 Friday\nadj push 2 Monday"
        self.adj("plan the backlog?")
        out = self.adj("yes", "2")
        self.assertIn("Moved #2", out)
        self.assertNotIn("Moved #1", out)


class Models(CLITestCase):
    def test_brief_without_a_model_prints_the_record(self):
        self.fake.task("Old thing", due="2026-09-01")
        out = self.adj("good morning")
        self.assertIn("OVERDUE", out)
        self.assertIn("#1", out)
        with self.db() as c:
            self.assertEqual(c.execute("SELECT kind, text FROM briefs").fetchone()[0], "morning")

    def test_brief_makes_one_call_with_the_packet_and_records_cost(self):
        self.with_model()
        self.fake.task("Old thing", due="2026-09-01")
        self.fake.reply = "OVERDUE\n- #1 (Old thing)"
        self.assertIn("#1 (Old thing)", self.adj("good morning"))
        self.assertEqual(len(self.fake.chat_requests), 1)
        request = self.fake.chat_requests[0]
        self.assertEqual(request["model"], "claude-opus-5-5")
        self.assertEqual(request["output_config"]["effort"], "medium")
        self.assertIn("Old thing", json.dumps(request["messages"]))
        self.assertIn("claude-opus-5-5", self.adj("spend"))

    def test_routes_change_per_job(self):
        self.assertIn("chat → claude-sonnet-5-5", self.adj("use", "sonnet", "for", "chat"))
        self.assertIn("claude-sonnet-5-5", self.adj("models"))

    def test_question_without_a_model_says_so(self):
        self.assertIn("no model is set up", self.adj("what should I focus on?"))


class Forgetting(CLITestCase):
    def test_stale_and_pushed_tasks_and_snooze(self):
        self.fake.task("Ancient task", due="2026-09-01")
        self.fake.task("Slippery task", due="2026-09-30")
        self.adj("tasks")
        for day in ("Friday", "Monday", "next Friday"):
            self.adj("push", "2", day)
        out = self.adj("what am I forgetting")
        self.assertIn("overdue 29 days", out)
        self.assertIn("pushed 3 times", out)
        self.assertIn("Snoozed finding 1", self.adj("snooze 1 for 7 days because waiting on the client"))
        self.assertNotIn("Ancient task", self.adj("what am I forgetting"))
        with self.db() as c:
            self.assertEqual(c.execute("SELECT reason FROM snoozes").fetchone()[0], "waiting on the client")


class People(CLITestCase):
    def test_who_is_reads_an_oversoul_folder(self):
        folder = self.home / "oversoul" / "people"
        folder.mkdir(parents=True)
        (folder / "dana-example.md").write_text("# Dana Example, Example Co\n\n## Status\nActive client.\n")
        (self.home / ".config" / "adjutant" / "people-dir").write_text(str(self.home / "oversoul"))
        self.assertIn("Active client.", self.adj("who is Dana Example"))
        self.assertIn("No profile matches", self.adj("who is Zed"))

    def test_who_is_without_a_folder_explains(self):
        self.assertIn("No people folder is set", self.adj("who is Dana"))


class Session(CLITestCase):
    def test_pasted_command_list_runs_line_by_line(self):
        self.fake.task("One")
        self.fake.task("Two")
        self.adj("tasks")
        out = self.adj(stdin="adj 1 done\n")
        self.assertIn("Completed #1", out)

    def test_status_and_version(self):
        self.assertIn("Todoist:  connected", self.adj("status"))
        self.assertRegex(self.adj("--version"), r"\d+\.\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
