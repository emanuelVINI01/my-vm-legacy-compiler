import unittest

from compiler.compiler import Compiler


class TestConditionals(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_simple_if_true(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 5 > 3:
        x = 1
    y = 2
""")
        self.assertIn("JGT", asm)
        self.assertIn("JMP", asm)
        self.assertIn(":", asm)  # has labels

    def test_if_else(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    a = 10
    b = 5
    if a > b:
        x = 1
    else:
        x = 2
""")
        lines = asm.split("\n")
        jmp_count = sum(1 for l in lines if l.strip().startswith("JMP"))
        self.assertGreaterEqual(jmp_count, 2)

    def test_if_else_less_than(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 3 < 8:
        x = 1
    else:
        x = 2
""")
        self.assertIn("JLT", asm)

    def test_if_else_equal(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    if 5 == 5:
        x = 1
    else:
        x = 2
""")
        self.assertIn("JEQ", asm)

    def test_if_without_else(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    a = 1
    if a < 10:
        a = a + 1
""")
        lines = asm.split("\n")
        cond_cmps = [l for l in lines if "JLT" in l or "JGT" in l or "JEQ" in l or "JNE" in l]
        self.assertGreaterEqual(len(cond_cmps), 1)

    def test_if_with_compound_condition(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10
    y = 20
    if x != y:
        z = 1
    else:
        z = 0
""")
        self.assertIn("JNE", asm)


if __name__ == "__main__":
    unittest.main()