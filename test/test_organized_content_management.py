import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import organization_service


class OrganizedContentManagementTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name) / "organized"
        self.root.mkdir()
        self.root_patch = patch.object(
            organization_service,
            "ORGANIZED_ROOT_DIR",
            str(self.root),
        )
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)

    def test_lists_and_deletes_organized_file(self):
        file_path = self.root / "journal" / "entry.md"
        file_path.parent.mkdir()
        file_path.write_text("entry", encoding="utf-8")

        self.assertEqual(organization_service.list_organized_files(), ["journal/entry.md"])
        organization_service.delete_organized_file("journal/entry.md")
        self.assertFalse(file_path.exists())

    def test_deletes_top_level_folder_and_all_contents(self):
        folder = self.root / "journal"
        nested_file = folder / "nested" / "entry.md"
        nested_file.parent.mkdir(parents=True)
        nested_file.write_text("entry", encoding="utf-8")

        organization_service.delete_organized_folder("journal")
        self.assertFalse(folder.exists())

    def test_rejects_paths_outside_organized_root(self):
        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("keep", encoding="utf-8")

        with self.assertRaises(ValueError):
            organization_service.delete_organized_file("../outside.md")

        self.assertTrue(outside.exists())

    def test_rejects_nested_folder_deletion(self):
        nested_folder = self.root / "journal" / "nested"
        nested_folder.mkdir(parents=True)

        with self.assertRaises(ValueError):
            organization_service.delete_organized_folder("journal/nested")

        self.assertTrue(nested_folder.exists())

    def test_rejects_symlinked_content(self):
        outside = Path(self.temp_dir.name) / "outside.md"
        outside.write_text("keep", encoding="utf-8")
        link = self.root / "outside-link.md"
        link.symlink_to(outside)

        with self.assertRaises(ValueError):
            organization_service.delete_organized_file("outside-link.md")

        self.assertTrue(outside.exists())
        self.assertTrue(link.is_symlink())


if __name__ == "__main__":
    unittest.main()
