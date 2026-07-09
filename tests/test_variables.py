import unittest

from compiler.compiler import Compiler


class TestVariables(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_simple_assignment(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 42
""")
        self.assertIn("SET", asm)
        self.assertIn("42", asm)

    def test_variable_reassignment(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10
    x = 20
""")
        set_count = sum(1 for l in asm.split("\n") if l.strip().startswith("SET"))
        self.assertGreaterEqual(set_count, 2)

    def test_variable_copy(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10
    y = x
""")
        self.assertIn("SET", asm)

    def test_variable_with_expression(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 5
    y = x + 3
""")
        has_add = any("ADD" in l for l in asm.split("\n"))
        self.assertTrue(has_add)

    def test_variable_int_metadata(self):
        self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 42
""")
        info = self.compiler.ctx.get_var_info("x")
        self.assertEqual(info["type"], "int")

    def test_augmented_addition(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 0
    x += 1
""")
        has_add = any("ADD" in l for l in asm.split("\n"))
        self.assertTrue(has_add)

    def test_augmented_subtraction(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10
    x -= 3
""")
        has_sub = any("SUB" in l for l in asm.split("\n"))
        self.assertTrue(has_sub)

    def test_multiple_variables(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    a = 1
    b = 2
    c = 3
    d = a + b
""")
        self.assertIn("SET A 1;", asm)
        self.assertIn("SET B 2;", asm)
        self.assertIn("SET C 3;", asm)


if __name__ == "__main__":
    unittest.main()