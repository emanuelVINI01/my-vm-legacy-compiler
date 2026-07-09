import unittest

from compiler.compiler import Compiler


class TestLists(unittest.TestCase):
    def setUp(self):
        Compiler.reset_instance()
        self.compiler = Compiler()

    def compile_and_get(self, code):
        return self.compiler.compile(code)

    def test_array_creation(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [10, 20, 30]
""")
        store_count = sum(1 for l in asm.split("\n") if l.strip().startswith("STORE"))
        self.assertGreaterEqual(store_count, 3)

    def test_array_base_address_in_register(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [1, 2, 3]
""")
        self.assertIn("SET", asm)

    def test_array_index_access(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [10, 20, 30]
    x = arr[0]
""")
        has_load = any("LOAD" in l for l in asm.split("\n"))
        self.assertTrue(has_load)

    def test_array_store(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [0, 0, 0]
    arr[0] = 99
""")
        has_store = any("STORE" in l for l in asm.split("\n"))
        self.assertTrue(has_store)

    def test_array_with_variable_index(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [1, 2, 3]
    i = 0
    x = arr[i]
""")
        has_load = any("LOAD" in l for l in asm.split("\n"))
        self.assertTrue(has_load)

    def test_array_in_loop(self):
        asm = self.compile_and_get("""from myvm_lib import entry_point

@entry_point
def main():
    arr = [0, 0, 0]
    i = 0
    while i < 3:
        arr[i] = i
        i += 1
""")
        self.assertIn("STORE", asm)
        self.assertIn("JLT", asm)


if __name__ == "__main__":
    unittest.main()