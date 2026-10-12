import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp_server import server


class MCPServerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "organized"
        self.root.mkdir()
        self.root_patch = patch.object(server, "ORGANIZED_ROOT", self.root)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_lists_folders_and_markdown_files(self):
        nested = self.root / "journal" / "2026"
        nested.mkdir(parents=True)
        (nested / "entry.md").write_text("# Journal", encoding="utf-8")
        (nested / "ignored.txt").write_text("not exposed", encoding="utf-8")

        self.assertEqual(server.list_folders(), ["journal", "journal/2026"])
        self.assertEqual(server.list_files(), ["journal/2026/entry.md"])
        self.assertEqual(server.list_files("journal"), ["journal/2026/entry.md"])

    def test_reads_markdown_and_rejects_non_markdown(self):
        markdown = self.root / "journal.md"
        markdown.write_text("# Note", encoding="utf-8")
        (self.root / "secret.txt").write_text("secret", encoding="utf-8")

        self.assertEqual(server.read_file("journal.md"), "# Note")
        with self.assertRaises(ValueError):
            server.read_file("secret.txt")

    def test_rejects_traversal_and_symlinks(self):
        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        link = self.root / "linked.md"
        link.symlink_to(outside)

        with self.assertRaises(ValueError):
            server.read_file("../outside.md")
        with self.assertRaises(ValueError):
            server.read_file("linked.md")
        self.assertEqual(server.list_files(), [])


if __name__ == "__main__":
    unittest.main()
