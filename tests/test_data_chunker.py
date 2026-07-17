import unittest

from modules.data_chunker import DataChunker


class TestDataChunker(unittest.TestCase):
    def setUp(self):
        self.chunker = DataChunker(max_chunk_size=50)

    def test_clean_text_removes_comments_and_extra_whitespace(self):
        raw = "int main() {\n/* comentario */\n\n\n  return   0;\n}"
        cleaned = self.chunker.clean_text(raw)
        self.assertNotIn("/*", cleaned)
        self.assertNotIn("\n\n\n", cleaned)

    def test_split_into_chunks_respects_max_size_when_possible(self):
        text = "\n".join("line_%s" % i for i in range(20))
        chunks = self.chunker.split_into_chunks(text)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), self.chunker.max_chunk_size + 10)

    def test_split_into_chunks_short_text_returns_single_chunk(self):
        text = "short text"
        chunks = self.chunker.split_into_chunks(text)
        self.assertEqual(chunks, [text])

    def test_chunk_functions_builds_header_per_function(self):
        data = {
            "decompiled": [
                {"name": "func_a", "entry_point": "0x1000", "code": "int func_a() { return 1; }"},
            ]
        }
        chunks = self.chunker.chunk_functions(data)
        self.assertEqual(len(chunks), 1)
        self.assertIn("func_a", chunks[0])
        self.assertIn("0x1000", chunks[0])


if __name__ == "__main__":
    unittest.main()
