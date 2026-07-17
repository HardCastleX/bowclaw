"""Orquestador de Ingenieria Inversa - punto de entrada principal."""
import asyncio
import glob
import json
import logging
import os
import sys

from dotenv import load_dotenv

from modules.ghidra_runner import GhidraRunner
from modules.data_chunker import DataChunker
from modules.gemini_client import GeminiClient
from utils.logger import setup_logging

logger = logging.getLogger(__name__)


class ReverseEngineeringOrchestrator:
    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)

        self.ghidra_runner = GhidraRunner(
            ghidra_path=os.environ["GHIDRA_PATH"],
            project_dir=self.config["workspace"]["temp_projects"],
        )
        self.chunker = DataChunker(max_chunk_size=self.config["max_chunk_size"])
        self.gemini_client = GeminiClient(
            api_key=os.environ["GEMINI_API_KEY"],
            model=self.config.get("gemini_model", "gemini-3.5-flash"),
            pro_model=self.config.get("gemini_pro_model", "gemini-3.1-pro-preview"),
        )

    def _load_config(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def run_ghidra_analysis(self, binary_path):
        binary_name = os.path.splitext(os.path.basename(binary_path))[0]
        output_path = os.path.join(
            self.config["workspace"]["temp_projects"], "%s_extracted.json" % binary_name
        )
        self.ghidra_runner.run_headless_analysis(
            binary_path, "extractor.py", output_path
        )
        return output_path

    def chunk_extracted_data(self, extracted_json_path):
        data = self.chunker.load_raw_data(extracted_json_path)
        return self.chunker.chunk_functions(data)

    def analyze_with_gemini(self, chunks, use_pro=False):
        return asyncio.run(self.gemini_client.analyze_all_chunks(chunks, use_pro=use_pro))

    def generate_report(self, binary_path, analysis_results):
        binary_name = os.path.splitext(os.path.basename(binary_path))[0]
        report_path = os.path.join(
            self.config["workspace"]["reports"], "%s_report.md" % binary_name
        )

        lines = ["# Reporte de Ingenieria Inversa: %s" % binary_name, ""]
        for i, result in enumerate(analysis_results, start=1):
            lines.append("## Fragmento %s" % i)
            if isinstance(result, Exception):
                lines.append("_Error durante el analisis: %s_" % result)
            else:
                lines.append(result)
            lines.append("")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return report_path

    def run(self, binary_path):
        logger.info("Iniciando analisis de: %s", binary_path)

        extracted_json_path = self.run_ghidra_analysis(binary_path)
        logger.info("Extraccion de Ghidra completada: %s", extracted_json_path)

        chunks = self.chunk_extracted_data(extracted_json_path)
        logger.info("Datos troceados en %s chunks", len(chunks))

        analysis_results = self.analyze_with_gemini(chunks)
        logger.info("Analisis con Gemini completado")

        report_path = self.generate_report(binary_path, analysis_results)
        logger.info("Reporte generado: %s", report_path)

        return report_path


def _resolve_binary_path(config):
    if len(sys.argv) > 1:
        return sys.argv[1]

    input_dir = config["workspace"]["input"]
    candidates = [
        f for f in glob.glob(os.path.join(input_dir, "*"))
        if os.path.basename(f) != ".gitkeep"
    ]
    if not candidates:
        raise SystemExit(
            "No se especifico un binario y no hay ninguno en %s" % input_dir
        )
    if len(candidates) > 1:
        raise SystemExit(
            "Hay multiples binarios en %s; especifica uno como argumento" % input_dir
        )
    return candidates[0]


def main():
    setup_logging()
    load_dotenv()

    orchestrator = ReverseEngineeringOrchestrator()
    binary_path = _resolve_binary_path(orchestrator.config)
    report_path = orchestrator.run(binary_path)

    print("Reporte generado en: %s" % report_path)


if __name__ == "__main__":
    main()
