import unittest

from compiler.compiler import Compiler


class TestPrints(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_print_int_variable(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print

@entry_point
def main():
    x = 42
    print(x)
""")
        lines = asm.split("\n")
        print_lines = [l for l in lines if l.strip().startswith("PRINT ") and "CHAR" not in l]
        self.assertGreaterEqual(len(print_lines), 1)

    def test_print_int_literal(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print

@entry_point
def main():
    print(42)
""")
        self.assertIn("PRINT 42;", asm)

    def test_print_string_variable(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print

@entry_point
def main():
    s = "hello"
    print(s)
""")
        self.assertIn("WRITE", asm)
        self.assertIn("PRINTCHAR 10;", asm)

    def test_print_string_literal(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print

@entry_point
def main():
    print("hello")
""")
        self.assertIn("WRITESTR", asm)
        self.assertIn("PRINTCHAR 10;", asm)

    def test_print_str_with_variable(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    s = "hello"
    print_str(s)
""")
        self.assertIn("WRITE", asm)

    def test_print_str_with_literal_still_works(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    print_str("hello")
""")
        self.assertIn("WRITESTR", asm)

    def test_mixed_print_and_print_str(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print, print_str

@entry_point
def main():
    x = 10
    s = "ok"
    print(x)
    print_str(s)
""")
        self.assertIn("PRINT", asm)
        self.assertIn("WRITE", asm)


if __name__ == "__main__":
    unittest.main()