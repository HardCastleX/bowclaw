"""Modulo encargado de invocar Ghidra en modo headless."""
import logging
import os
import shutil
import subprocess
import threading

logger = logging.getLogger(__name__)


class GhidraRunError(Exception):
    pass


class GhidraRunner:
    def __init__(self, ghidra_path, project_dir, scripts_dir="ghidra_scripts", verbose=False):
        self.ghidra_path = ghidra_path
        self.project_dir = project_dir
        self.scripts_dir = scripts_dir
        self.verbose = verbose

    def run_headless_analysis(self, binary_path, script_name, output_path, timeout=600):
        os.makedirs(self.project_dir, exist_ok=True)
        project_name = os.path.splitext(os.path.basename(binary_path))[0]

        command = self._build_command(
            binary_path, script_name, output_path, project_name
        )
        logger.info("Running Ghidra headless: %s", " ".join(command))

        try:
            output_lines, returncode, timed_out = self._stream_process(command, timeout)

            if timed_out:
                raise GhidraRunError(
                    "Ghidra headless analysis timed out after %ss" % timeout
                )

            if returncode != 0:
                tail = "\n".join(output_lines[-30:])
                raise GhidraRunError(
                    "Ghidra headless analysis failed (code %s). Ultimas lineas:\n%s"
                    % (returncode, tail)
                )

            return output_path
        finally:
            self.cleanup_project(project_name)

    def _stream_process(self, command, timeout):
        """Ejecuta el proceso mostrando su output en vivo (INFO si verbose,
        DEBUG si no) mientras lo captura completo para diagnostico de errores."""
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        timed_out_flag = {"value": False}

        def _kill_on_timeout():
            timed_out_flag["value"] = True
            process.kill()

        timer = threading.Timer(timeout, _kill_on_timeout)
        timer.start()

        output_lines = []
        try:
            for line in process.stdout:
                line = line.rstrip("\n")
                output_lines.append(line)
                if self.verbose:
                    logger.info("[ghidra] %s", line)
                else:
                    logger.debug("[ghidra] %s", line)
            process.wait()
        finally:
            timer.cancel()

        return output_lines, process.returncode, timed_out_flag["value"]

    def cleanup_project(self, project_name):
        """Elimina artefactos residuales del proyecto en project_dir.

        -deleteProject ya limpia el proyecto en el caso exitoso; esto cubre
        los casos de timeout/error donde Ghidra no llega a hacer esa limpieza.
        """
        for suffix in (".gpr", ".rep"):
            path = os.path.join(self.project_dir, project_name + suffix)
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.isfile(path):
                os.remove(path)

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
