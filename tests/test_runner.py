import unittest
import subprocess
import os
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VM_BINARY = os.path.join(PROJECT_ROOT, "target", "debug", "my-vm")
COMPILER_MAIN = os.path.join(PROJECT_ROOT, "vm-compiler", "main.py")
VM_NOISE = "Failed to create server-side surface decoration: Missing\n"


def _clean_vm_output(output):
    return output.replace(VM_NOISE, "")


def compile_and_run(source_code):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(source_code)
        py_path = f.name

    asm_path = py_path.rsplit(".", 1)[0] + ".asm"

    try:
        subprocess.run(
            ["python3", COMPILER_MAIN, py_path, asm_path],
            capture_output=True, text=True, check=True
        )

        result = subprocess.run(
            [VM_BINARY, asm_path],
            capture_output=True, text=True, check=True
        )
        return _clean_vm_output(result.stdout)
    finally:
        for p in [py_path, asm_path]:
            if os.path.exists(p):
                os.unlink(p)


def compile_and_run_multifile(main_content, extra_files):
    tmpdir = tempfile.mkdtemp()
    try:
        main_path = os.path.join(tmpdir, "main.py")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(main_content)

        for filename, content in extra_files.items():
            filepath = os.path.join(tmpdir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

        asm_path = os.path.join(tmpdir, "output.asm")

        subprocess.run(
            ["python3", COMPILER_MAIN, main_path, asm_path],
            capture_output=True, text=True, check=True
        )

        result = subprocess.run(
            [VM_BINARY, asm_path],
            capture_output=True, text=True, check=True
        )
        return _clean_vm_output(result.stdout)
    finally:
        for root, dirs, files in os.walk(tmpdir, topdown=False):
            for name in files:
                os.unlink(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(tmpdir)


@unittest.skipIf(not os.path.exists(VM_BINARY), "VM binary not found. Run 'cargo build' first.")
class TestEndToEnd(unittest.TestCase):
    def test_print_str(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    print_str("Hello World")
""")
        self.assertEqual(output, "Hello World\n")

    def test_variable_and_print(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 42
    print_str("OK")
""")
        self.assertEqual(output, "OK\n")

    def test_if_else_true_branch(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    if 5 > 3:
        print_str("YES")
    else:
        print_str("NO")
""")
        self.assertEqual(output, "YES\n")

    def test_if_else_false_branch(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    if 5 < 3:
        print_str("YES")
    else:
        print_str("NO")
""")
        self.assertEqual(output, "NO\n")

    def test_while_loop_counter(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 0
    while x < 3:
        x += 1
    print_str("DONE")
""")
        self.assertEqual(output, "DONE\n")

    def test_equality_check(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 10
    if x == 10:
        print_str("EQUAL")
""")
        self.assertEqual(output, "EQUAL\n")

    def test_not_equal_check(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 5
    if x != 10:
        print_str("NOT_EQUAL")
""")
        self.assertEqual(output, "NOT_EQUAL\n")

    def test_custom_function_call(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    hello()

def hello():
    print_str("HI")
""")
        self.assertEqual(output, "HI\n")

    def test_function_with_args(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    greet(1)

def greet(x):
    print_str("OK")
""")
        self.assertEqual(output, "OK\n")

    def test_array_creation_and_access(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    print_str("OK")
""")
        self.assertEqual(output, "OK\n")

    def test_for_loop(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    for i in range(3):
        x = 1
    print_str("DONE")
""")
        self.assertEqual(output, "DONE\n")

    def test_boolop_and(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 10
    y = 5
    if x > 3 and y < 10:
        print_str("OK")
""")
        self.assertEqual(output, "OK\n")

    def test_boolop_or(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 1
    y = 20
    if x > 10 or y > 5:
        print_str("OK")
""")
        self.assertEqual(output, "OK\n")

    def test_string_variable_print_str(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str

@entry_point
def main():
    bom_dia = "tudo bem?"
    print_str(bom_dia)
""")
        self.assertEqual(output, "tudo bem?\n")

    def test_print_int_variable(self):
        output = compile_and_run("""from myvm_lib import entry_point, print

@entry_point
def main():
    add = 2
    print(add)
""")
        self.assertEqual(output, "2\n")

    def test_user_code_full(self):
        output = compile_and_run("""from myvm_lib import entry_point, print_str, print

@entry_point
def main():
    bom_dia = "tudo bem?"
    print_str(bom_dia)
    add = 2
    while add < 20:
        add += 2
        print_str("Resultado: ")
        print(add)
""")
        self.assertIn("tudo bem?", output)
        self.assertIn("Resultado:", output)

    def test_import_util_module_call(self):
        output = compile_and_run_multifile(
            """from myvm_lib import entry_point, print_str
import util

@entry_point
def main():
    util.say_hi()
""",
            {"util.py": """from myvm_lib import print_str

def say_hi():
    print_str("HI_FROM_UTIL")
"""}
        )
        self.assertEqual(output, "HI_FROM_UTIL\n")

    def test_from_import_named(self):
        output = compile_and_run_multifile(
            """from myvm_lib import entry_point, print_str
from math_util import add

@entry_point
def main():
    result = add(2, 3)
    if result == 5:
        print_str("OK")
""",
            {"math_util.py": """def add(a, b):
    result = a + b
    return result
"""}
        )
        self.assertEqual(output, "OK\n")


if __name__ == "__main__":
    unittest.main()