import unittest

from compiler.compiler import Compiler


class TestCompilerIntegration(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_empty_main(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    pass
""")
        self.assertIn("main:", asm)
        self.assertIn("HALT;", asm)

    def test_print_str(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    print_str("Test")
""")
        self.assertIn('WRITESTR "Test";', asm)
        self.assertIn("WRITE", asm)
        self.assertIn("PRINTCHAR 10;", asm)
        self.assertIn("HALT;", asm)

    def test_function_named_main_no_decorator(self):
        asm = self.compile_and_get("""from myvm_lib import print_str

def main():
    print_str("Works")
""")
        self.assertIn('WRITESTR "Works";', asm)

    def test_counter_program(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    count = 0
    while count < 5:
        count += 1
""")
        self.assertIn("while_start", asm)
        self.assertIn("JLT", asm)
        self.assertIn("HALT;", asm)

    def test_conditional_program(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 10
    if x > 5:
        y = 1
    else:
        y = 0
""")
        self.assertIn("JMP", asm)
        self.assertIn("HALT;", asm)

    def test_factorial_program(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    n = 5
    result = 1
    while n > 1:
        result = result * n
        n = n - 1
""")
        self.assertIn("JGT", asm)
        self.assertIn("MUL", asm)

    def test_singleton_returns_same_instance(self):
        c1 = Compiler()
        c2 = Compiler()
        self.assertIs(c1, c2)

    def test_singleton_reset(self):
        c1 = Compiler()
        Compiler.reset_instance()
        c2 = Compiler()
        self.assertIsNot(c1, c2)

    def test_output_ends_with_halt(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 1
""")
        lines = asm.strip().split("\n")
        self.assertEqual(lines[-1], "HALT;")

    def test_custom_function_emitted_after_halt(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    foo()

def foo():
    x = 5
""")
        self.assertIn("CALL foo;", asm)
        halt_pos = asm.index("HALT;")
        func_pos = asm.index("foo:")
        self.assertGreater(func_pos, halt_pos)

    def test_for_range_generates_loop(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    for i in range(10):
        x = i
""")
        self.assertIn("for_start", asm)
        self.assertIn("for_natural_end", asm)
        self.assertIn("JLT", asm)

    def test_and_condition_generates_labels(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    x = 5
    y = 3
    if x > 0 and y < 10:
        z = 1
""")
        self.assertIn("and_test", asm)
        self.assertIn("JGT", asm)
        self.assertIn("JLT", asm)

    def test_array_creation_generates_stores(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [1, 2, 3, 4]
""")
        store_lines = [l for l in asm.split("\n") if l.strip().startswith("STORE")]
        self.assertGreaterEqual(len(store_lines), 4)


if __name__ == "__main__":
    unittest.main()