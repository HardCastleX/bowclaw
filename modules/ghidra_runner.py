"""Modulo encargado de invocar Ghidra en modo headless."""
import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class GhidraRunError(Exception):
    pass


class GhidraRunner:
    def __init__(self, ghidra_path, project_dir, scripts_dir="ghidra_scripts"):
        self.ghidra_path = ghidra_path
        self.project_dir = project_dir
        self.scripts_dir = scripts_dir

    def run_headless_analysis(self, binary_path, script_name, output_path, timeout=600):
        os.makedirs(self.project_dir, exist_ok=True)
        project_name = os.path.splitext(os.path.basename(binary_path))[0]

        command = self._build_command(
            binary_path, script_name, output_path, project_name
        )
        logger.info("Running Ghidra headless: %s", " ".join(command))

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise GhidraRunError(
                "Ghidra headless analysis timed out after %ss" % timeout
            ) from exc

        if result.returncode != 0:
            raise GhidraRunError(
                "Ghidra headless analysis failed (code %s): %s"
                % (result.returncode, result.stderr)
            )

        logger.debug("Ghidra stdout: %s", result.stdout)
        return output_path

    def _build_command(self, binary_path, script_name, output_path, project_name):
        return [
            self.ghidra_path,
            self.project_dir,
            project_name,
            "-import", binary_path,
            "-scriptPath", self.scripts_dir,
            "-postScript", script_name, output_path,
            "-deleteProject",
        ]
