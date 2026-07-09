import unittest

from compiler.emitter import CodeEmitter


class TestCodeEmitter(unittest.TestCase):
    def setUp(self):
        self.emitter = CodeEmitter()

    def test_emit_simple(self):
        self.emitter.emit("SET", "A", 5)
        self.assertEqual(self.emitter.get_output(), "SET A 5;")

    def test_emit_multiple(self):
        self.emitter.emit("SET", "A", 10)
        self.emitter.emit("SET", "B", 20)
        self.emitter.emit("ADD", "A", "B")
        expected = "SET A 10;\nSET B 20;\nADD A B;"
        self.assertEqual(self.emitter.get_output(), expected)

    def test_emit_label(self):
        self.emitter.emit_label("main")
        self.emitter.emit("HALT")
        expected = "main:\nHALT;"
        self.assertEqual(self.emitter.get_output(), expected)

    def test_emit_comment(self):
        self.emitter.emit_comment("this is a comment")
        self.assertEqual(self.emitter.get_output(), "// this is a comment")

    def test_emit_string_literal(self):
        self.emitter.emit("WRITESTR", '"Hello"')
        self.assertEqual(self.emitter.get_output(), 'WRITESTR "Hello";')

    def test_emit_raw(self):
        self.emitter.emit_raw("custom: raw text")
        self.emitter.emit("HALT")
        expected = "custom: raw text\nHALT;"
        self.assertEqual(self.emitter.get_output(), expected)

    def test_get_lines(self):
        self.emitter.emit("SET", "A", 1)
        self.emitter.emit("HALT")
        lines = self.emitter.get_lines()
        self.assertEqual(lines, ["SET A 1;", "HALT;"])

    def test_emit_with_register_operands(self):
        self.emitter.emit("JGT", "A", "B", "loop_start")
        self.assertEqual(self.emitter.get_output(), "JGT A B loop_start;")


if __name__ == "__main__":
    unittest.main()