import unittest

from compiler.context import CompilationContext, SCRATCH_REGISTER, RETURN_REGISTER
from compiler.emitter import CodeEmitter


class TestCompilationContext(unittest.TestCase):
    def setUp(self):
        self.emitter = CodeEmitter()
        self.ctx = CompilationContext()
        self.ctx.set_emitter(self.emitter)

    def test_allocate_first_register(self):
        reg = self.ctx.allocate_register("x")
        self.assertEqual(reg, "A")

    def test_allocate_second_register(self):
        reg_a = self.ctx.allocate_register("x")
        reg_b = self.ctx.allocate_register("y")
        self.assertEqual(reg_a, "A")
        self.assertEqual(reg_b, "B")

    def test_same_variable_gets_same_register(self):
        reg1 = self.ctx.allocate_register("count")
        reg2 = self.ctx.allocate_register("count")
        self.assertEqual(reg1, reg2)

    def test_get_register_raises_for_undefined(self):
        with self.assertRaises(NameError):
            self.ctx.get_register("undefined_var")

    def test_skips_scratch_and_return_registers(self):
        registers = set()
        for i in range(24):
            reg = self.ctx.allocate_register(f"var_{i}")
            registers.add(reg)
        self.assertNotIn(SCRATCH_REGISTER, registers)
        self.assertNotIn(RETURN_REGISTER, registers)

    def test_variable_metadata_stored(self):
        self.ctx.allocate_register("x", var_type="string", length=9)
        info = self.ctx.get_var_info("x")
        self.assertEqual(info["reg"], "A")
        self.assertEqual(info["type"], "string")
        self.assertEqual(info["len"], 9)

    def test_variable_metadata_defaults_to_int(self):
        self.ctx.allocate_register("x")
        info = self.ctx.get_var_info("x")
        self.assertEqual(info["type"], "int")
        self.assertEqual(info["len"], 0)

    def test_get_register_returns_only_register(self):
        self.ctx.allocate_register("x", var_type="string", length=5)
        reg = self.ctx.get_register("x")
        self.assertEqual(reg, "A")
        self.assertIsInstance(reg, str)

    def test_label_counter_increments(self):
        lbl1 = self.ctx.new_label("loop")
        lbl2 = self.ctx.new_label("loop")
        self.assertEqual(lbl1, "loop_1")
        self.assertEqual(lbl2, "loop_2")

    def test_emit_delegates_to_emitter(self):
        self.ctx.emit("SET", "X", 42)
        self.assertIn("SET X 42;", self.emitter.get_output())

    def test_emit_label_delegates_to_emitter(self):
        self.ctx.emit_label("start")
        self.assertIn("start:", self.emitter.get_output())


if __name__ == "__main__":
    unittest.main()