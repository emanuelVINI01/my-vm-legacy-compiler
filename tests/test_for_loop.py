import unittest

from compiler.compiler import Compiler


class TestForLoop(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_for_range_end_only(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    for i in range(5):
        print_str("X")
""")
        self.assertIn("for_start", asm)
        self.assertIn("JLT", asm)
        self.assertIn("ADD", asm)
        self.assertIn("for_natural_end", asm)

    def test_for_range_start_end(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    for i in range(0, 3):
        print_str("X")
""")
        self.assertIn("for_start", asm)
        self.assertIn("JLT", asm)

    def test_for_with_body_variables(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    s = 0
    for i in range(10):
        s += i
""")
        self.assertIn("for_start", asm)
        self.assertIn("ADD", asm)

    def test_for_nested_in_if(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 5
    if x > 0:
        for i in range(3):
            print_str("X")
""")
        self.assertIn("for_start", asm)
        self.assertIn("JGT", asm)

    def test_for_with_variable_end(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    n = 5
    for i in range(n):
        x = i
""")
        self.assertIn("for_start", asm)


if __name__ == "__main__":
    unittest.main()