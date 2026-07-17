"""Configuracion centralizada de logging para el orquestador."""
import logging
import os


def setup_logging(log_dir="workspace/reports", level=logging.INFO):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "orchestrator.log")

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [file_handler, console_handler]

    return root_logger
