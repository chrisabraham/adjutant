"""The backup restores, and the release check catches what it should."""

import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("gpg"), "gpg isn't installed")
class Backup(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="adjutant-backup-"))
        self.env = {**os.environ, "HOME": str(self.home), "GNUPGHOME": str(self.home / ".gnupg")}
        self.env.pop("XDG_CONFIG_HOME", None)
        self.env.pop("XDG_DATA_HOME", None)
        (self.home / ".gnupg").mkdir(mode=0o700)
        config = self.home / ".config" / "adjutant"
        config.mkdir(parents=True)
        (config / "backup-passphrase").write_text("correct horse battery staple\n")
        data = self.home / ".local" / "share" / "adjutant"
        data.mkdir(parents=True)
        with sqlite3.connect(data / "adjutant.sqlite3") as c:
            c.execute("CREATE TABLE t (x TEXT)")
            c.execute("INSERT INTO t VALUES ('kept')")

    def tearDown(self):
        shutil.rmtree(self.home)

    def run_backup(self, *args):
        return subprocess.run(["bash", str(REPO / "tools" / "backup.sh"), *args], env=self.env,
                              capture_output=True, text=True, timeout=60)

    def test_backup_is_encrypted_and_restores(self):
        result = self.run_backup()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("restore tested", result.stdout)
        made = list((self.home / ".local/share/adjutant/backups").glob("*.gpg"))
        self.assertEqual(len(made), 1)
        self.assertNotIn(b"kept", made[0].read_bytes())
        target = self.home / "restored.sqlite3"
        self.assertEqual(self.run_backup("--restore", str(made[0]), str(target)).returncode, 0)
        with sqlite3.connect(target) as c:
            self.assertEqual(c.execute("SELECT x FROM t").fetchone()[0], "kept")

    def test_no_passphrase_refuses(self):
        (self.home / ".config/adjutant/backup-passphrase").unlink()
        result = self.run_backup()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no passphrase", result.stderr)


class ReleaseCheck(unittest.TestCase):
    def run_check(self, root, denylist=None):
        work = Path(tempfile.mkdtemp(prefix="adjutant-release-"))
        self.addCleanup(shutil.rmtree, work)
        (work / "tools").mkdir()
        shutil.copy(REPO / "tools" / "release_check.py", work / "tools")
        for name, text in root.items():
            (work / name).write_text(text)
        env = {**os.environ, "ADJUTANT_DENYLIST": str(work / "deny.txt")}
        if denylist:
            (work / "deny.txt").write_text(denylist)
        return subprocess.run(["python3", str(work / "tools" / "release_check.py"), "--all"], env=env,
                              capture_output=True, text=True, cwd=work)

    def test_clean_tree_passes(self):
        result = self.run_check({"a.md": "Nothing to see. Write to you@example.com.\n"})
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_catches_generic_leaks(self):
        result = self.run_check({"a.md": "key sk-ant-" + "x" * 30 + "\nserver " + ".".join(["203", "0", "113", "9"]) + "\n"
                                          "path /home/" + "someone/notes\nmail some.one" + "@corp.test\n"})
        self.assertEqual(result.returncode, 1)
        for label in ("Anthropic key", "IP address", "home path", "email address"):
            self.assertIn(label, result.stdout)

    def test_catches_denylisted_names(self):
        result = self.run_check({"a.md": "Met with Example Client Corp today.\n"}, "# private\nexample client\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("denylisted: example client", result.stdout)

    def test_the_repo_itself_is_clean(self):
        result = subprocess.run(["python3", str(REPO / "tools" / "release_check.py")], cwd=REPO,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
