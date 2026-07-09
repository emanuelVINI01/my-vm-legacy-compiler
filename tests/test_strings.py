import unittest

from compiler.compiler import Compiler


class TestStrings(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_string_assignment_emits_writestr(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = "hello"
""")
        self.assertIn("WRITESTR", asm)
        self.assertIn('"hello"', asm)

    def test_string_assignment_emits_getlastaddr(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = "hello"
""")
        self.assertIn("GETLASTADDR", asm)

    def test_string_assignment_emits_sub_for_pointer(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = "hello"
""")
        self.assertIn("SUB", asm)

    def test_string_metadata_stored(self):
        self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = "hello"
""")
        info = self.compiler.ctx.get_var_info("x")
        self.assertEqual(info["type"], "string")
        self.assertEqual(info["len"], 5)

    def test_int_metadata_default(self):
        self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 42
""")
        info = self.compiler.ctx.get_var_info("x")
        self.assertEqual(info["type"], "int")
        self.assertEqual(info["len"], 0)

    def test_multiple_strings(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    a = "abc"
    b = "def"
""")
        writestr_count = asm.count("WRITESTR")
        self.assertGreaterEqual(writestr_count, 2)

    def test_string_copy_preserves_metadata(self):
        self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    a = "hello"
    b = a
""")
        info_b = self.compiler.ctx.get_var_info("b")
        self.assertEqual(info_b["type"], "string")
        self.assertEqual(info_b["len"], 5)


if __name__ == "__main__":
    unittest.main()