import unittest

from compiler.compiler import Compiler


class TestFunctions(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_simple_call_no_args(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    hello()

def hello():
    print_str("HI")
""")
        self.assertIn("CALL hello;", asm)
        self.assertIn("hello:", asm)
        self.assertIn("JMP Z;", asm)

    def test_call_with_args(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    greet("X")

def greet(name):
    print_str("OK")
""")
        self.assertIn("CALL greet;", asm)
        self.assertIn("greet:", asm)
        self.assertIn("JMP Z;", asm)

    def test_multiple_functions(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    a()

def a():
    b()

def b():
    print_str("OK")
""")
        self.assertIn("CALL a;", asm)
        self.assertIn("CALL b;", asm)
        self.assertIn("a:", asm)
        self.assertIn("b:", asm)

    def test_function_after_halt(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    hello()

def hello():
    print_str("HI")
""")
        halt_pos = asm.index("HALT;")
        func_pos = asm.index("hello:")
        self.assertGreater(func_pos, halt_pos)

    def test_function_with_multiple_args(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    compute(1, 2)

def compute(a, b):
    print_str("OK")
""")
        self.assertIn("compute:", asm)
        self.assertIn("CALL compute;", asm)

    def test_function_returns(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    do_work()

def do_work():
    x = 1
""")
        self.assertIn("JMP Z;", asm)


if __name__ == "__main__":
    unittest.main()