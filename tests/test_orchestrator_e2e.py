"""
Prueba end-to-end del pipeline completo, simulando las dos dependencias
externas (Ghidra y la API de Gemini) ya que no siempre estan disponibles
en el entorno de desarrollo.
"""
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from main import ReverseEngineeringOrchestrator

FAKE_EXTRACTED_DATA = {
    "program_name": "sample.exe",
    "functions": [
        {"name": "main", "entry_point": "0x401000", "signature": "int main(void)"},
        {"name": "check_license", "entry_point": "0x401050", "signature": "int check_license(char *)"},
    ],
    "decompiled": [
        {"name": "main", "entry_point": "0x401000", "code": "int main(void) {\n  return check_license(\"key\");\n}"},
        {"name": "check_license", "entry_point": "0x401050", "code": "int check_license(char *key) {\n  return strcmp(key, \"SECRET\") == 0;\n}"},
    ],
}


class TestOrchestratorEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.workspace = os.path.join(self.tmp_dir, "workspace")
        for sub in ("input", "temp_projects", "reports"):
            os.makedirs(os.path.join(self.workspace, sub))

        self.config_path = os.path.join(self.tmp_dir, "config.json")
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump({
                "max_chunk_size": 4000,
                "workspace": {
                    "input": os.path.join(self.workspace, "input"),
                    "temp_projects": os.path.join(self.workspace, "temp_projects"),
                    "reports": os.path.join(self.workspace, "reports"),
                },
            }, f)

        self.binary_path = os.path.join(self.workspace, "input", "sample.exe")
        with open(self.binary_path, "wb") as f:
            f.write(b"\x00fake-binary-bytes")

        self.env_patch = patch.dict(os.environ, {
            "GHIDRA_PATH": "C:\\fake\\ghidra\\analyzeHeadless.bat",
            "GEMINI_API_KEY": "fake-key",
        })
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    @patch("main.GeminiClient.analyze_all_chunks")
    @patch("main.GhidraRunner.run_headless_analysis")
    def test_full_pipeline_produces_report(self, mock_ghidra, mock_gemini):
        def fake_ghidra_run(binary_path, script_name, output_path, timeout=600):
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(FAKE_EXTRACTED_DATA, f)
            return output_path

        mock_ghidra.side_effect = fake_ghidra_run

        async def fake_analyze(chunks, use_pro=False):
            return [
                "Esta funcion es el punto de entrada del programa." for _ in chunks
            ]

        mock_gemini.side_effect = fake_analyze

        orchestrator = ReverseEngineeringOrchestrator(config_path=self.config_path)
        report_path = orchestrator.run(self.binary_path)

        self.assertTrue(os.path.isfile(report_path))
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Reporte de Ingenieria Inversa: sample", content)
        self.assertIn("Fragmento 1", content)
        self.assertIn("punto de entrada", content)
        mock_ghidra.assert_called_once()
        mock_gemini.assert_called_once()


if __name__ == "__main__":
    unittest.main()
