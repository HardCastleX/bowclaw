"""Modulo encargado de trocear y limpiar la data extraida de Ghidra."""
import json
import re


class DataChunker:
    def __init__(self, max_chunk_size=4000):
        self.max_chunk_size = max_chunk_size

    def load_raw_data(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def clean_text(self, raw_text):
        text = re.sub(r"/\*.*?\*/", "", raw_text, flags=re.DOTALL)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def split_into_chunks(self, text):
        if len(text) <= self.max_chunk_size:
            return [text]

        chunks = []
        current = []
        current_len = 0

        for line in text.split("\n"):
            line_len = len(line) + 1
            if current_len + line_len > self.max_chunk_size and current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
            current.append(line)
            current_len += line_len

        if current:
            chunks.append("\n".join(current))

        return chunks

    def chunk_functions(self, extracted_data):
        """Convierte el JSON de extractor.py en chunks de texto listos para DeepSeek."""
        chunks = []
        for entry in extracted_data.get("decompiled", []):
            header = "// Function: %s @ %s\n" % (
                entry["name"], entry["entry_point"]
            )
            cleaned = self.clean_text(entry["code"])
            for piece in self.split_into_chunks(cleaned):
                chunks.append(header + piece)
        return chunks
