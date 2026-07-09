import unittest

from compiler.compiler import Compiler


class TestLoops(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_simple_while(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 0
    while x < 5:
        x = x + 1
""")
        self.assertIn("while_start", asm)
        self.assertIn("JLT", asm)

    def test_while_with_greater_than(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10
    while x > 0:
        x = x - 1
""")
        self.assertIn("JGT", asm)

    def test_while_labels_are_unique(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 0
    while x < 3:
        x = x + 1
    while x > 0:
        x = x - 1
""")
        start_labels = [l.strip() for l in asm.split("\n") if l.strip().startswith("while_start") and l.strip().endswith(":")]
        self.assertEqual(len(start_labels), 2)
        self.assertNotEqual(start_labels[0], start_labels[1])

    def test_while_with_variable_comparison(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 0
    limit = 10
    while x < limit:
        x = x + 1
""")
        self.assertIn("JLT", asm)

    def test_while_with_equality_check(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 0
    while x != 10:
        x = x + 1
""")
        self.assertIn("JNE", asm)


if __name__ == "__main__":
    unittest.main()