import ast
import os
from .emitter import CodeEmitter
from .context import CompilationContext
from .linker import Linker
from .visitors.functions import FunctionVisitor


class Compiler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._reset()

    def _reset(self):
        self.emitter = CodeEmitter()
        self.ctx = CompilationContext()
        self.ctx.set_emitter(self.emitter)
        self.func_visitor = FunctionVisitor(self.ctx)

    @classmethod
    def reset_instance(cls):
        cls._instance = None

    def compile(self, source_code):
        self._reset()
        tree = ast.parse(source_code)
        modules = [("main", "", tree)]
        self.emitter.emit_label("main")
        self.func_visitor.visit_modules(modules)
        return self.emitter.get_output()

    def compile_file(self, input_path):
        self._reset()
        abs_path = os.path.abspath(input_path)
        base_dir = os.path.dirname(abs_path)

        linker = Linker(base_dir)
        modules = linker.resolve(abs_path)

        self.emitter.emit_label("main")
        self.func_visitor.visit_modules(modules)
        return self.emitter.get_output()