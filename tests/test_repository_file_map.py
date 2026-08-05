"""Tests that the repository file map stays complete as the project evolves."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FILE_MAP = PROJECT_ROOT / "docs" / "repository_file_map.md"


class RepositoryFileMapTests(unittest.TestCase):
    def test_map_covers_all_tracked_and_pending_project_files(self) -> None:
        completed = subprocess.run(
            [
                "git",
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
            ],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        expected_paths = {
            line for line in completed.stdout.splitlines() if line.strip()
        }
        contents = FILE_MAP.read_text(encoding="utf-8")
        mapped_paths = {
            match
            for match in re.findall(r"^\| ([^|]+) \|", contents, flags=re.MULTILINE)
            if match not in {"路径", "---"}
        }
        self.assertSetEqual(expected_paths, mapped_paths)

    def test_map_states_the_maintenance_rule(self) -> None:
        contents = FILE_MAP.read_text(encoding="utf-8")
        self.assertIn("维护规则", contents)
        self.assertIn("同一提交中更新本表", contents)


if __name__ == "__main__":
    unittest.main()
