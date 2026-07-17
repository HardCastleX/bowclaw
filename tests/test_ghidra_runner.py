import unittest
from unittest.mock import patch, MagicMock

from modules.ghidra_runner import GhidraRunner, GhidraRunError


class FakeProcess:
    def __init__(self, lines, returncode=0):
        self._lines = list(lines)
        self.returncode = returncode
        self.killed = False

    @property
    def stdout(self):
        def generator():
            for line in self._lines:
                if self.killed:
                    return
                yield line
        return generator()

    def kill(self):
        self.killed = True
        self.returncode = -9

    def wait(self):
        pass


class FakeTimerFiresImmediately:
    """Simula que el timeout ya se cumplio antes de leer el stdout."""

    def __init__(self, timeout, func):
        self.func = func

    def start(self):
        self.func()

    def cancel(self):
        pass


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

    @patch("modules.ghidra_runner.subprocess.Popen")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_success(self, mock_makedirs, mock_popen):
        mock_popen.return_value = FakeProcess(["linea 1", "linea 2"], returncode=0)
        result = self.runner.run_headless_analysis(
            "workspace/input/sample.exe", "extractor.py", "out.json"
        )
        self.assertEqual(result, "out.json")

    @patch("modules.ghidra_runner.subprocess.Popen")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_nonzero_exit_raises(self, mock_makedirs, mock_popen):
        mock_popen.return_value = FakeProcess(["boom"], returncode=1)
        with self.assertRaises(GhidraRunError):
            self.runner.run_headless_analysis(
                "workspace/input/sample.exe", "extractor.py", "out.json"
            )

    @patch("modules.ghidra_runner.threading.Timer", new=FakeTimerFiresImmediately)
    @patch("modules.ghidra_runner.subprocess.Popen")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_timeout_raises(self, mock_makedirs, mock_popen):
        mock_popen.return_value = FakeProcess(["linea 1", "linea 2"], returncode=0)
        with self.assertRaises(GhidraRunError):
            self.runner.run_headless_analysis(
                "workspace/input/sample.exe", "extractor.py", "out.json", timeout=1
            )

    @patch("modules.ghidra_runner.subprocess.Popen")
    @patch("modules.ghidra_runner.os.makedirs")
    def test_run_headless_analysis_verbose_logs_at_info(self, mock_makedirs, mock_popen):
        mock_popen.return_value = FakeProcess(["hola desde ghidra"], returncode=0)
        verbose_runner = GhidraRunner(
            ghidra_path="/fake/analyzeHeadless",
            project_dir="workspace/temp_projects",
            verbose=True,
        )
        with self.assertLogs("modules.ghidra_runner", level="INFO") as cm:
            verbose_runner.run_headless_analysis(
                "workspace/input/sample.exe", "extractor.py", "out.json"
            )
        self.assertTrue(any("hola desde ghidra" in msg for msg in cm.output))

    @patch("modules.ghidra_runner.shutil.rmtree")
    @patch("modules.ghidra_runner.os.path.isdir", return_value=True)
    def test_cleanup_project_removes_residual_dirs(self, mock_isdir, mock_rmtree):
        self.runner.cleanup_project("sample")
        self.assertEqual(mock_rmtree.call_count, 2)  # .gpr y .rep


if __name__ == "__main__":
    unittest.main()
