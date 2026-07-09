import unittest

from compiler.compiler import Compiler


class TestBoolOps(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_and_both_true(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 10
    y = 5
    if x > 3 and y < 10:
        print_str("OK")
""")
        self.assertIn("JGT", asm)
        self.assertIn("JLT", asm)

    def test_and_first_false(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 1
    y = 5
    if x > 3 and y < 10:
        print_str("NO")
    else:
        print_str("YES")
""")
        self.assertIn("JGT", asm)

    def test_or_both_false(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 1
    y = 20
    if x > 10 or y < 5:
        print_str("TRUE")
    else:
        print_str("FALSE")
""")
        self.assertIn("JGT", asm)
        self.assertIn("JLT", asm)

    def test_or_first_true(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 20
    y = 1
    if x > 10 or y > 5:
        print_str("TRUE")
""")
        self.assertIn("JGT", asm)

    def test_and_with_equality(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    a = 5
    b = 5
    if a == b and a < 10:
        print_str("OK")
""")
        self.assertIn("JEQ", asm)
        self.assertIn("JLT", asm)

    def test_or_with_not_equals(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    a = 10
    b = 5
    if a != b or a > 20:
        print_str("OK")
""")
        self.assertIn("JNE", asm)

    def test_and_in_while(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 0
    y = 10
    while x < 5 and y > 0:
        x += 1
        y -= 1
""")
        self.assertIn("while_start", asm)
        self.assertIn("JLT", asm)
        self.assertIn("JGT", asm)


if __name__ == "__main__":
    unittest.main()