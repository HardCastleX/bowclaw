import subprocess
import unittest
from unittest.mock import patch, MagicMock

from modules.ghidra_runner import GhidraRunner, GhidraRunError


class TestGhidraRunner(unittest.TestCase):
    def setUp(self):
        self.runner = GhidraRunner(
            ghidra_path="/fake/analyzeHeadless",
            project_dir="workspace/temp_projects",
        )

    def test_build_command_includes_required_flags(self):
        command = self.runner._build_command(
            "workspace/input/sample.exe", "extractor.py", "out.json", "sample"
        )
        self.assertIn("-import", command)
        self.assertIn("-postScript", command)
        self.assertIn("-deleteProject", command)
        self.assertIn("workspace/input/sample.exe", command)

    @patch("modules.ghidra_runner.subprocess.run")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_success(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        result = self.runner.run_headless_analysis(
            "workspace/input/sample.exe", "extractor.py", "out.json"
        )
        self.assertEqual(result, "out.json")

    @patch("modules.ghidra_runner.subprocess.run")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_nonzero_exit_raises(self, mock_makedirs, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="boom")
        with self.assertRaises(GhidraRunError):
            self.runner.run_headless_analysis(
                "workspace/input/sample.exe", "extractor.py", "out.json"
            )

    @patch("modules.ghidra_runner.subprocess.run")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_timeout_raises(self, mock_makedirs, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="ghidra", timeout=1)
        with self.assertRaises(GhidraRunError):
            self.runner.run_headless_analysis(
                "workspace/input/sample.exe", "extractor.py", "out.json", timeout=1
            )

    @patch("modules.ghidra_runner.shutil.rmtree")
    @patch("modules.ghidra_runner.os.path.isdir", return_value=True)
    def test_cleanup_project_removes_residual_dirs(self, mock_isdir, mock_rmtree):
        self.runner.cleanup_project("sample")
        self.assertEqual(mock_rmtree.call_count, 2)  # .gpr y .rep


if __name__ == "__main__":
    unittest.main()
