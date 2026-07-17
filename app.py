"""App Streamlit para el Orquestador de Ingenieria Inversa."""
import json
import logging
import os

import streamlit as st
from dotenv import load_dotenv

from main import ReverseEngineeringOrchestrator
from utils.logger import setup_logging

CONFIG_PATH = "config.json"


class StreamlitLogHandler(logging.Handler):
    """Actualiza un placeholder de Streamlit en vivo con cada linea de log.

    Como Ghidra (subprocess sincrono) y el analisis LLM (asyncio.run, bloqueante
    dentro del mismo hilo) corren en el hilo principal del script de Streamlit,
    cada llamada a logger.info/debug dispara este handler de inmediato y el
    placeholder se actualiza en el navegador sin necesitar threads separados.
    """

    def __init__(self, placeholder, max_lines=400):
        super().__init__()
        self.placeholder = placeholder
        self.max_lines = max_lines
        self.lines = []

    def emit(self, record):
        self.lines.append(self.format(record))
        self.placeholder.code("\n".join(self.lines[-self.max_lines:]), language="text")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_provider_choice(config, provider):
    config["llm_provider"] = provider
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


def save_uploaded_binary(config, uploaded_file):
    input_dir = config["workspace"]["input"]
    os.makedirs(input_dir, exist_ok=True)
    binary_path = os.path.join(input_dir, uploaded_file.name)
    with open(binary_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return binary_path


def main():
    st.set_page_config(page_title="Orquestador de Ingenieria Inversa", layout="wide")
    st.title("Orquestador de Ingenieria Inversa")
    st.caption("Ghidra (headless) + LLM configurable -> reporte de analisis")

    config = load_config()
    providers = list(config.get("providers", {}).keys()) or ["gemini"]
    current_provider = config.get("llm_provider", providers[0])
    default_index = providers.index(current_provider) if current_provider in providers else 0

    col_upload, col_provider = st.columns([3, 1])
    with col_upload:
        uploaded_file = st.file_uploader("Binario a analizar", type=None)
    with col_provider:
        provider = st.selectbox("Proveedor LLM", providers, index=default_index)

    analyze_clicked = st.button(
        "Analizar", type="primary", disabled=uploaded_file is None
    )

    log_placeholder = st.empty()
    status_placeholder = st.empty()
    report_placeholder = st.container()

    if analyze_clicked and uploaded_file is not None:
        save_provider_choice(config, provider)
        binary_path = save_uploaded_binary(config, uploaded_file)

        root_logger = setup_logging(level=logging.DEBUG)
        handler = StreamlitLogHandler(log_placeholder)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        root_logger.addHandler(handler)

        status_placeholder.info("Corriendo pipeline (Ghidra -> chunking -> LLM -> reporte)...")

        try:
            load_dotenv(override=True)
            orchestrator = ReverseEngineeringOrchestrator(config_path=CONFIG_PATH, verbose=True)
            report_path = orchestrator.run(binary_path)

            status_placeholder.success("Completado: %s" % report_path)

            with open(report_path, "r", encoding="utf-8") as f:
                report_content = f.read()

            with report_placeholder:
                st.markdown("## Reporte")
                st.download_button(
                    "Descargar reporte",
                    report_content,
                    file_name=os.path.basename(report_path),
                    mime="text/markdown",
                )
                st.markdown(report_content)
        except Exception as exc:
            status_placeholder.error("Error durante el analisis: %s" % exc)
        finally:
            root_logger.removeHandler(handler)


if __name__ == "__main__":
    main()
