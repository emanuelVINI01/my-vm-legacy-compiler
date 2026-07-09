import ast
from .base import BaseVisitor


class ExpressionVisitor(BaseVisitor):
    def visit_BinOp(self, node):
        left_reg = self.visit(node.left)
        op_map = {
            ast.Add: "ADD",
            ast.Sub: "SUB",
            ast.Mult: "MUL",
            ast.Div: "DIV",
            ast.Mod: "MOD",
            ast.Pow: "POW",
            ast.BitXor: "XOR",
        }
        op = op_map.get(type(node.op))
        if op is None:
            raise NotImplementedError(f"Operator {type(node.op).__name__} not supported")

        right_reg = self.visit(node.right)
        temp_reg = self.ctx.allocate_temp("expr_temp")
        self.ctx.emit_copy(temp_reg, left_reg)
        self.ctx.emit(op, temp_reg, right_reg)
        return temp_reg

    def visit_Compare(self, node):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise NotImplementedError("Only single comparisons are supported")

        op = node.ops[0]
        left_reg = self.visit(node.left)
        right = node.comparators[0]

        if isinstance(right, ast.Constant):
            right_reg = self.ctx.allocate_temp("cmp_val")
            self.ctx.emit("SET", right_reg, right.value)
        else:
            right_reg = self.visit(right)

        return left_reg, right_reg, op

    def visit_BoolOp(self, node):
        from ..patterns import CodegenPatterns
        patterns = CodegenPatterns(self.ctx)
        return patterns.compile_boolop(node, self)

    def visit_Subscript(self, node):
        base_reg = self.visit(node.value)
        index = node.slice

        addr_reg = self.ctx.allocate_temp("arr_addr")
        self.ctx.emit_copy(addr_reg, base_reg)

        if isinstance(index, ast.Constant):
            idx_reg = self.ctx.allocate_temp("arr_idx")
            self.ctx.emit("SET", idx_reg, index.value)
        else:
            idx_reg = self.visit(index)

        self.ctx.emit("ADD", addr_reg, idx_reg)

        result_reg = self.ctx.allocate_temp("arr_val")
        self.ctx.emit("LOAD", result_reg, addr_reg)
        return result_reg

    def visit_List(self, node):
        base_addr = self.ctx.ram_offset
        base_reg = self.ctx.allocate_temp("list_base")
        self.ctx.emit("SET", base_reg, base_addr)

        for elt in node.elts:
            if isinstance(elt, ast.Constant):
                val_reg = self.ctx.allocate_temp("list_val")
                self.ctx.emit("SET", val_reg, elt.value)
            else:
                val_reg = self.visit(elt)
            self.ctx.emit("STORE", base_addr, val_reg)
            base_addr += 1

        self.ctx.ram_offset = base_addr
        return base_reg

    def visit_Call(self, node):
        target = self.ctx.resolve_call_target(node.func)
        if target is None:
            func_name = ""
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                func_name = node.func.attr
            raise NotImplementedError(
                f"Function '{func_name}' not supported in expressions"
            )

        if target == "str":
            return self._compile_str_cast(node)

        if target in self.ctx.function_registry:
            return self._compile_call(target, node)

        raise NotImplementedError(f"Function '{target}' not supported in expressions")

    def _compile_str_cast(self, node):
        if len(node.args) != 1:
            raise ValueError("str() takes exactly 1 argument")
        
        arg = node.args[0]
        val_reg = self.visit(arg)
        
        addr_reg = self.ctx.allocate_temp("itoa_addr")
        len_reg = self.ctx.allocate_temp("itoa_len")
        
        base_addr = self.ctx.ram_offset
        self.ctx.emit("SET", addr_reg, base_addr)
        self.ctx.emit("ITOA", val_reg, addr_reg, len_reg)
        
        self.ctx.ram_offset += 12
        
        return {"type": "dynamic_string", "reg": addr_reg, "len_reg": len_reg}

    def _compile_call(self, func_name, node):
        func_info = self.ctx.get_function(func_name)
        params = func_info["params"]
        args = node.args

        arg_regs = ["A", "B", "C", "D", "E"]
        for i, arg in enumerate(args):
            if i >= len(arg_regs):
                raise NotImplementedError("Too many function arguments (max 5)")
            target_reg = arg_regs[i]
            if isinstance(arg, ast.Constant):
                if isinstance(arg.value, str):
                    length = len(arg.value)
                    self.ctx.emit("WRITESTR", f'"{arg.value}"')
                    self.ctx.emit("GETLASTADDR", target_reg)
                    if length > 0:
                        temp = self.ctx.allocate_temp("arg_len")
                        self.ctx.emit("SET", temp, length - 1)
                        self.ctx.emit("SUB", target_reg, temp)
                else:
                    self.ctx.emit("SET", target_reg, arg.value)
            elif isinstance(arg, ast.Name):
                src = self.ctx.get_register(arg.id)
                self.ctx.emit_copy(target_reg, src)
            else:
                val_reg = self.visit(arg)
                self.ctx.emit_copy(target_reg, val_reg)

        self.ctx.emit("CALL", func_info["label"])
        result_reg = self.ctx.allocate_temp("call_ret")
        self.ctx.emit_copy(result_reg, "A")
        return result_reg

    def visit_Name(self, node):
        return self.ctx.get_register(node.id)

    def visit_Constant(self, node):
        temp_reg = self.ctx.allocate_temp("const")
        self.ctx.emit("SET", temp_reg, node.value)
        return temp_reg