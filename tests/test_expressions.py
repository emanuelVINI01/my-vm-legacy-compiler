import unittest

from compiler.compiler import Compiler


class TestExpressions(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_greater_than(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 10 > 5:
        x = 1
""")
        self.assertIn("JGT", asm)
        self.assertIn("JMP", asm)
        self.assertIn("HALT;", asm)

    def test_less_than(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 3 < 8:
        x = 1
""")
        self.assertIn("JLT", asm)

    def test_equal(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 5 == 5:
        x = 1
""")
        self.assertIn("JEQ", asm)

    def test_not_equal(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 5 != 3:
        x = 1
""")
        self.assertIn("JNE", asm)

    def test_comparison_with_variables(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    a = 10
    b = 5
    if a > b:
        c = 1
""")
        self.assertIn("JGT A B", asm.replace(" ", " "))

    def test_addition_expression(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 5 + 3
""")
        self.assertIn("ADD", asm)

    def test_subtraction_expression(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10 - 3
""")
        self.assertIn("SUB", asm)

    def test_multiplication_expression(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 4 * 5
""")
        self.assertIn("MUL", asm)

    def test_division_expression(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 20 / 4
""")
        self.assertIn("DIV", asm)


if __name__ == "__main__":
    unittest.main()