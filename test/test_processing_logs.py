import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services import organization_service, processing_log_service


class ProcessingLogTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.raw_dir = self.root / "raw-markdown"
        self.raw_dir.mkdir()
        self.raw_file = self.raw_dir / "entry.md"
        self.raw_file.write_text("raw content", encoding="utf-8")
        self.patches = [
            patch.object(organization_service, "RAW_MARKDOWN_DIR", str(self.raw_dir)),
            patch.object(
                processing_log_service,
                "PROCESSING_LOG_DB",
                str(self.root / "logs" / "processing.sqlite3"),
            ),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_success_is_persisted_before_raw_file_is_removed(self):
        transform = patch.object(
            organization_service,
            "transform_and_organize_markdown",
            return_value=(True, "Output saved"),
        )
        transform.start()
        self.addCleanup(transform.stop)
        original_remove = os.remove

        def verify_log_then_remove(path):
            logs = processing_log_service.list_processing_logs()
            self.assertEqual(logs[0]["status"], "Processing succeeded")
            self.assertEqual(logs[0]["source_removed"], 0)
            original_remove(path)

        remove = patch.object(organization_service.os, "remove", side_effect=verify_log_then_remove)
        remove.start()
        self.addCleanup(remove.stop)

        self.assertTrue(
            organization_service.process_raw_markdown(
                "entry.md", "model", "prompt.md", "journal"
            )
        )
        self.assertFalse(self.raw_file.exists())

        log = processing_log_service.list_processing_logs()[0]
        self.assertEqual(log["status"], "Success")
        self.assertEqual(log["source_removed"], 1)
        self.assertEqual(log["target_folder"], "journal")

    def test_failed_processing_keeps_raw_file_and_persists_failure(self):
        transform = patch.object(
            organization_service,
            "transform_and_organize_markdown",
            return_value=(False, "Model unavailable"),
        )
        transform.start()
        self.addCleanup(transform.stop)

        self.assertFalse(
            organization_service.process_raw_markdown(
                "entry.md", "model", "prompt.md", "journal"
            )
        )
        self.assertTrue(self.raw_file.exists())

        log = processing_log_service.list_processing_logs()[0]
        self.assertEqual(log["status"], "Failed")
        self.assertEqual(log["message"], "Model unavailable")
        self.assertEqual(log["source_removed"], 0)

    def test_cleanup_failure_is_logged_and_keeps_raw_file(self):
        transform = patch.object(
            organization_service,
            "transform_and_organize_markdown",
            return_value=(True, "Output saved"),
        )
        transform.start()
        self.addCleanup(transform.stop)
        remove = patch.object(
            organization_service.os,
            "remove",
            side_effect=OSError("permission denied"),
        )
        remove.start()
        self.addCleanup(remove.stop)

        self.assertFalse(
            organization_service.process_raw_markdown(
                "entry.md", "model", "prompt.md", "journal"
            )
        )
        self.assertTrue(self.raw_file.exists())

        log = processing_log_service.list_processing_logs()[0]
        self.assertEqual(log["status"], "Cleanup failed")
        self.assertIn("permission denied", log["message"])
        self.assertEqual(log["source_removed"], 0)


if __name__ == "__main__":
    unittest.main()
