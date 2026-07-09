import unittest
import os
import tempfile

from compiler.linker import Linker


class TestLinker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                os.unlink(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.tmpdir)

    def _write(self, filename, content):
        path = os.path.join(self.tmpdir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_single_file_no_imports(self):
        path = self._write("main.py", "x = 1\ndef main(): pass\n")
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0][0], "main")

    def test_import_module(self):
        self._write("util.py", "def foo(): pass\n")
        path = self._write("main.py", "import util\ndef main(): util.foo()\n")
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        module_names = [m[0] for m in modules]
        self.assertIn("main", module_names)
        self.assertIn("util", module_names)
        self.assertEqual(len(modules), 2)

    def test_from_import(self):
        self._write("math.py", "def add(): pass\ndef sub(): pass\n")
        path = self._write("main.py", "from math import add\ndef main(): add()\n")
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        module_names = [m[0] for m in modules]
        self.assertIn("main", module_names)
        self.assertIn("math", module_names)

    def test_ignores_myvm_lib(self):
        path = self._write("main.py",
            "from myvm_lib import entry_point, print_str\n"
            "@entry_point\ndef main(): print_str('OK')\n"
        )
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        self.assertEqual(len(modules), 1)

    def test_recursive_imports(self):
        self._write("c.py", "def foo(): pass\n")
        self._write("b.py", "import c\ndef bar(): c.foo()\n")
        path = self._write("a.py", "import b\ndef main(): b.bar()\n")
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        self.assertEqual(len(modules), 3)

    def test_topological_order(self):
        self._write("c.py", "def foo(): pass\n")
        self._write("b.py", "import c\ndef bar(): c.foo()\n")
        path = self._write("a.py", "import b\ndef main(): b.bar()\n")
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        names = [m[0] for m in modules]
        self.assertIn("main", names)
        c_index = names.index("c")
        b_index = names.index("b")
        self.assertLess(c_index, b_index)  # c has no deps, should come before b

    def test_circular_import_detected(self):
        self._write("b.py", "import a\n")
        path = self._write("a.py", "import b\ndef main(): pass\n")
        linker = Linker(self.tmpdir)
        with self.assertRaises(RuntimeError):
            linker.resolve(path)

    def test_path_resolution(self):
        self._write("util.py", "def foo(): pass\n")
        path = self._write("main.py", "import util\ndef main(): util.foo()\n")
        linker = Linker(self.tmpdir)
        modules = linker.resolve(path)
        util = [m for m in modules if m[0] == "util"]
        self.assertEqual(len(util), 1)
        self.assertTrue(os.path.exists(util[0][1]))

    def test_module_name_mangling(self):
        from compiler.context import CompilationContext
        ctx = CompilationContext()
        mangled = ctx.mangle_name("util", "calcular")
        self.assertEqual(mangled, "util_calcular")

    def test_main_name_not_mangled(self):
        from compiler.context import CompilationContext
        ctx = CompilationContext()
        mangled = ctx.mangle_name("main", "foo")
        self.assertEqual(mangled, "foo")


if __name__ == "__main__":
    unittest.main()