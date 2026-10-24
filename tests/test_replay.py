"""Pattern 2: replay real phrasings and check each lands where it should.

phrases.tsv is the record of how you talk to it. When a phrasing goes to the model
that should have been a command, add it here first, then fix the router.
"""

import unittest
from pathlib import Path

from fakes import CLITestCase

PHRASES = [line.split("\t", 1) for line in (Path(__file__).parent / "phrases.tsv").read_text().splitlines()
           if line.strip() and not line.startswith("#")]
CHAT_MARK = "no model is set up"


class Replay(CLITestCase):
    def test_every_phrase_routes_as_recorded(self):
        self.fake.task("First", due="2026-09-29")
        self.fake.task("Second")
        self.fake.task("Third")
        self.adj("tasks")
        wrong = []
        for route, phrase in PHRASES:
            went_to_chat = CHAT_MARK in self.adj(phrase)
            if went_to_chat != (route == "chat"):
                wrong.append(f"{route}\t{phrase}")
        self.assertEqual(wrong, [], "routed differently than recorded")


if __name__ == "__main__":
    unittest.main()
