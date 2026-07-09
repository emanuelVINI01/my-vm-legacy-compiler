import ast
from .base import BaseVisitor
from .expressions import ExpressionVisitor
from ..patterns import CodegenPatterns


class StatementVisitor(BaseVisitor):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.patterns = CodegenPatterns(ctx)
        self.expr_visitor = ExpressionVisitor(ctx)

    def visit_Assign(self, node):
        if len(node.targets) != 1:
            raise NotImplementedError("Only single-target assignment is supported")

        target = node.targets[0]

        if isinstance(target, ast.Subscript):
            self._compile_array_store(target, node.value)
            self.ctx.free_all_temps()
            return

        if not isinstance(target, ast.Name):
            raise NotImplementedError("Only simple variable assignment is supported")

        var_name = target.id

        if isinstance(node.value, ast.List):
            self._compile_array_creation(var_name, node.value)
            self.ctx.free_all_temps()
            return

        if isinstance(node.value, ast.Call):
            target = self.ctx.resolve_call_target(node.value.func)
            
            if target == "str":
                result = self.expr_visitor.visit_Call(node.value)
                self.ctx.variables[var_name] = result
                self.ctx.free_all_temps()
                return
                
            if target in self.ctx.function_registry:
                result_reg = self.expr_visitor.visit_Call(node.value)
                reg = self.ctx.allocate_register(var_name)
                self.ctx.emit_copy(reg, result_reg)
                self.ctx.free_all_temps()
                return

        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            self._compile_string_assignment(var_name, node.value.value)
            self.ctx.free_all_temps()
            return

        reg = self.ctx.allocate_register(var_name)

        if isinstance(node.value, ast.Constant):
            self.ctx.emit("SET", reg, node.value.value)
        elif isinstance(node.value, ast.Name):
            src_reg = self.ctx.get_register(node.value.id)
            self.ctx.emit_copy(reg, src_reg)
            src_info = self.ctx.get_var_info(node.value.id)
            self.ctx.variables[var_name] = {
                "reg": reg, "type": src_info["type"], "len": src_info["len"]
            }
            self.ctx.free_all_temps()
            return
        elif isinstance(node.value, ast.BinOp):
            result_reg = self.expr_visitor.visit_BinOp(node.value)
            self.ctx.emit_copy(reg, result_reg)
        elif isinstance(node.value, ast.Subscript):
            result_reg = self.expr_visitor.visit_Subscript(node.value)
            self.ctx.emit_copy(reg, result_reg)
        else:
            raise NotImplementedError(
                f"Assignment from {type(node.value).__name__} not supported"
            )
        self.ctx.free_all_temps()

    def _compile_string_assignment(self, var_name, text):
        reg = self.ctx.allocate_register(var_name, var_type="string", length=len(text))
        self.ctx.variables[var_name] = {"reg": reg, "type": "string", "len": len(text)}

        self.ctx.emit("WRITESTR", f'"{text}"')
        self.ctx.emit("GETLASTADDR", reg)
        if len(text) > 0:
            temp = self.ctx.allocate_temp("str_len")
            self.ctx.emit("SET", temp, len(text) - 1)
            self.ctx.emit("SUB", reg, temp)

    def _compile_array_creation(self, var_name, list_node):
        reg = self.ctx.allocate_register(var_name)
        self.ctx.register_array(var_name)

        base_addr = self.ctx.ram_offset
        self.ctx.emit("SET", reg, base_addr)

        for elt in list_node.elts:
            if isinstance(elt, ast.Constant):
                val_reg = self.ctx.allocate_temp("list_val")
                self.ctx.emit("SET", val_reg, elt.value)
            else:
                val_reg = self.expr_visitor.visit(elt)
            self.ctx.emit("STORE", base_addr, val_reg)
            base_addr += 1

        self.ctx.ram_offset = base_addr

    def _compile_array_store(self, target, value_node):
        base_reg = self.expr_visitor.visit(target.value)
        index = target.slice

        addr_reg = self.ctx.allocate_temp("arr_addr")
        self.ctx.emit_copy(addr_reg, base_reg)

        if isinstance(index, ast.Constant):
            idx_reg = self.ctx.allocate_temp("arr_idx")
            self.ctx.emit("SET", idx_reg, index.value)
        else:
            idx_reg = self.expr_visitor.visit(index)

        self.ctx.emit("ADD", addr_reg, idx_reg)

        if isinstance(value_node, ast.Constant):
            val_reg = self.ctx.allocate_temp("arr_stval")
            self.ctx.emit("SET", val_reg, value_node.value)
        elif isinstance(value_node, ast.Name):
            val_reg = self.ctx.get_register(value_node.id)
        else:
            val_reg = self.expr_visitor.visit(value_node)

        self.ctx.emit("STORE", addr_reg, val_reg)

    def visit_AugAssign(self, node):
        if not isinstance(node.target, ast.Name):
            raise NotImplementedError("Only simple variable augmented assignment is supported")

        var_name = node.target.id
        reg = self.ctx.allocate_register(var_name)

        op_map = {
            ast.Add: "ADD",
            ast.Sub: "SUB",
            ast.Mult: "MUL",
            ast.Div: "DIV",
        }
        op = op_map.get(type(node.op))
        if op is None:
            raise NotImplementedError(
                f"Augmented assignment operator {type(node.op).__name__} not supported"
            )

        if isinstance(node.value, ast.Constant):
            temp_reg = self.ctx.allocate_temp("aug_temp")
            self.ctx.emit("SET", temp_reg, node.value.value)
            self.ctx.emit(op, reg, temp_reg)
        elif isinstance(node.value, ast.Name):
            src_reg = self.ctx.get_register(node.value.id)
            self.ctx.emit(op, reg, src_reg)
        else:
            raise NotImplementedError(
                f"AugAssign with {type(node.value).__name__} not supported"
            )
        self.ctx.free_all_temps()

    def _compile_condition(self, test_node):
        if not isinstance(test_node, (ast.Compare, ast.BoolOp)):
            test_node = ast.Compare(
                left=test_node,
                ops=[ast.NotEq()],
                comparators=[ast.Constant(value=0)]
            )
            
        if isinstance(test_node, ast.Compare):
            result = self.expr_visitor.visit_Compare(test_node)
            left_reg, right_reg, op = result
            return self.patterns.compile_comparison(op, left_reg, right_reg)
        elif isinstance(test_node, ast.BoolOp):
            return self.patterns.compile_boolop(test_node, self.expr_visitor)
        else:
            raise NotImplementedError("Condition type not supported")

    def visit_If(self, node):
        true_label, false_label, end_label = self._compile_condition(node.test)

        self.patterns.compile_if(true_label, false_label, end_label)
        for stmt in node.body:
            self.visit(stmt)

        if node.orelse:
            self.patterns.compile_else(false_label, end_label)
            for stmt in node.orelse:
                self.visit(stmt)
            self.patterns.compile_endif(end_label)
        else:
            self.ctx.emit_label(false_label)
        self.ctx.free_all_temps()

    def visit_While(self, node):
        start_label = self.ctx.new_label("while_start")

        self.patterns.compile_while_start(start_label)

        true_lbl, false_lbl, _ = self._compile_condition(node.test)

        self.ctx.emit_label(true_lbl)
        self.ctx.push_loop(start_label, false_lbl)
        for stmt in node.body:
            self.visit(stmt)
        self.ctx.pop_loop()

        self.ctx.emit("JMP", start_label)

        self.ctx.emit_label(false_lbl)
        if node.orelse:
            for stmt in node.orelse:
                self.visit(stmt)
        self.ctx.free_all_temps()

    def visit_For(self, node):
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
            if node.iter.func.id == "range":
                self._compile_for_range(node)
                return
        raise NotImplementedError("Only 'for i in range(...)' loops are supported")

    def _compile_for_range(self, node):
        target_name = node.target.id
        counter_reg = self.ctx.allocate_register(target_name)

        args = node.iter.args
        start_val = None
        end_val = None

        if len(args) == 1:
            if isinstance(args[0], ast.Constant):
                end_val = args[0].value
            else:
                end_reg = self.expr_visitor.visit(args[0])
                end_val = end_reg
        elif len(args) >= 2:
            if isinstance(args[0], ast.Constant):
                start_val = args[0].value
            else:
                start_val = self.expr_visitor.visit(args[0])
            if isinstance(args[1], ast.Constant):
                end_val = args[1].value
            else:
                end_val = self.expr_visitor.visit(args[1])

        def visit_body():
            for stmt in node.body:
                self.visit(stmt)
                
        def visit_else():
            for stmt in node.orelse:
                self.visit(stmt)

        self.patterns.compile_for_range(
            counter_reg, start_val, end_val, self.expr_visitor, visit_body,
            has_else=bool(node.orelse), visit_else=visit_else
        )
        self.ctx.free_all_temps()
        
    def visit_Break(self, node):
        _, break_label = self.ctx.current_loop()
        self.ctx.emit("JMP", break_label)
        
    def visit_Continue(self, node):
        continue_label, _ = self.ctx.current_loop()
        self.ctx.emit("JMP", continue_label)

    def visit_Return(self, node):
        if node.value:
            if isinstance(node.value, ast.Constant):
                self.ctx.emit("SET", "A", node.value.value)
            elif isinstance(node.value, ast.Name):
                src = self.ctx.get_register(node.value.id)
                self.ctx.emit_copy("A", src)
            else:
                val_reg = self.expr_visitor.visit(node.value)
                self.ctx.emit_copy("A", val_reg)
        self.ctx.emit("JMP", "Z")

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            target = self.ctx.resolve_call_target(node.value.func)
            if target == "print_str":
                self._compile_print_str(node.value)
            elif target == "print":
                self._compile_print(node.value)
            elif target == "gui_update":
                self.ctx.emit("UPDATEGUI")
            elif target == "gui_draw_pixel":
                self._compile_gui_draw_pixel(node.value)
            elif target in self.ctx.function_registry:
                self._compile_void_call(target, node.value)
        self.generic_visit(node)

    def _compile_gui_draw_pixel(self, node):
        if len(node.args) != 3:
            raise ValueError("gui_draw_pixel requires exactly 3 arguments (x, y, color)")
        
        args_regs = []
        temp_names = []
        for arg in node.args:
            if isinstance(arg, ast.Name):
                args_regs.append(self.ctx.get_register(arg.id))
            elif isinstance(arg, ast.Constant):
                temp_name = f"_tmp_{self.ctx.label_counter}"
                self.ctx.label_counter += 1
                temp = self.ctx.allocate_register(temp_name)
                self.ctx.emit("SET", temp, arg.value)
                args_regs.append(temp)
                temp_names.append(temp_name)
            else:
                raise NotImplementedError("gui_draw_pixel arguments must be variables or constants")
                
        self.ctx.emit("DRAWPIXEL", args_regs[0], args_regs[1], args_regs[2])
        
        # Free constants
        for temp_name in temp_names:
            self.ctx.free_register(temp_name)

    def _compile_void_call(self, func_name, call_node):
        func_info = self.ctx.get_function(func_name)
        args = call_node.args
        arg_regs = ["A", "B", "C", "D", "E"]

        for i, arg in enumerate(args):
            if i >= len(arg_regs):
                raise NotImplementedError("Too many function arguments (max 5)")
            target_reg = arg_regs[i]
            if isinstance(arg, ast.Constant):
                self.ctx.emit("SET", target_reg, arg.value)
            elif isinstance(arg, ast.Name):
                src = self.ctx.get_register(arg.id)
                self.ctx.emit_copy(target_reg, src)
            else:
                val_reg = self.expr_visitor.visit(arg)
                self.ctx.emit_copy(target_reg, val_reg)

        self.ctx.emit("CALL", func_info["label"])

    def _compile_print(self, call_node):
        arg = call_node.args[0]

        if isinstance(arg, ast.Constant):
            if isinstance(arg.value, str):
                self._emit_print_string(arg.value)
            else:
                self.ctx.emit("PRINT", arg.value)
        elif isinstance(arg, ast.Name):
            info = self.ctx.get_var_info(arg.id)
            if info["type"] == "string":
                self.ctx.emit("WRITE", 1, info["reg"], info["len"])
                self.ctx.emit("PRINTCHAR", 10)
            elif info["type"] == "dynamic_string":
                self.ctx.emit("WRITE", 1, info["reg"], info["len_reg"])
                self.ctx.emit("PRINTCHAR", 10)
            else:
                self.ctx.emit("PRINT", info["reg"])
        elif isinstance(arg, ast.Call):
            func_name = ""
            if isinstance(arg.func, ast.Name):
                func_name = arg.func.id
            if func_name == "str":
                res = self.expr_visitor.visit_Call(arg)
                self.ctx.emit("WRITE", 1, res["reg"], res["len_reg"])
                self.ctx.emit("PRINTCHAR", 10)
                return
            raise NotImplementedError("print only supports variables, constants, and str()")
        else:
            raise NotImplementedError("print only supports variables, constants, and str()")

    def _compile_print_str(self, call_node):
        arg = call_node.args[0]
        
        if isinstance(arg, ast.Call):
            func_name = ""
            if isinstance(arg.func, ast.Name):
                func_name = arg.func.id
            if func_name == "str":
                res = self.expr_visitor.visit_Call(arg)
                self.ctx.emit("WRITE", 1, res["reg"], res["len_reg"])
                self.ctx.emit("PRINTCHAR", 10)
                return

        if isinstance(arg, ast.Name):
            info = self.ctx.get_var_info(arg.id)
            if info["type"] == "string":
                self.ctx.emit("WRITE", 1, info["reg"], info["len"])
                self.ctx.emit("PRINTCHAR", 10)
            elif info["type"] == "dynamic_string":
                self.ctx.emit("WRITE", 1, info["reg"], info["len_reg"])
                self.ctx.emit("PRINTCHAR", 10)
            else:
                raise NotImplementedError("print_str requires a string variable")
            return

        if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
            raise NotImplementedError("print_str only supports string literals or string variables")

        self._emit_print_string(arg.value)

    def _emit_print_string(self, s):
        length = len(s)
        self.ctx.emit("WRITESTR", f'"{s}"')
        addr_reg = self.ctx.allocate_temp("pr_addr")
        self.ctx.emit("GETLASTADDR", addr_reg)
        if length > 0:
            temp = self.ctx.allocate_temp("prlen")
            self.ctx.emit("SET", temp, length - 1)
            self.ctx.emit("SUB", addr_reg, temp)
        self.ctx.emit("WRITE", 1, addr_reg, length)
        self.ctx.emit("PRINTCHAR", 10)