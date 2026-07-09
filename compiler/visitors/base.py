import ast
from ..context import CompilationContext


class BaseVisitor(ast.NodeVisitor):
    def __init__(self, ctx: CompilationContext):
        self.ctx = ctx

    def resolve_value(self, node):
        if isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Name):
            return self.ctx.get_register(node.id)
        elif isinstance(node, ast.BinOp):
            return self._resolve_binop(node)
        else:
            raise NotImplementedError(f"Cannot resolve value of type {type(node).__name__}")

    def _resolve_binop(self, node):
        from .expressions import ExpressionVisitor
        expr_visitor = ExpressionVisitor(self.ctx)
        return expr_visitor.visit(node)

    def visit(self, node):
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, None)
        if visitor is not None:
            return visitor(node)
        return self.generic_visit(node)