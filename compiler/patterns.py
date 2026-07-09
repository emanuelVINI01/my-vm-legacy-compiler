class CodegenPatterns:
    def __init__(self, ctx):
        self.ctx = ctx

    def compile_comparison(self, op, left_reg, right_reg):
        true_label = self.ctx.new_label("cmp_true")
        false_label = self.ctx.new_label("cmp_false")
        end_label = self.ctx.new_label("cmp_end")

        jump_map = {
            "Gt": "JGT",
            "Lt": "JLT",
            "Eq": "JEQ",
            "NotEq": "JNE",
        }

        if isinstance(op, str):
            op_name = op
        else:
            op_name = type(op).__name__

        jump_op = jump_map.get(op_name)
        if jump_op is None:
            raise NotImplementedError(f"Comparison operator '{op_name}' not supported")

        self.ctx.emit(jump_op, left_reg, right_reg, true_label)
        self.ctx.emit("JMP", false_label)

        return true_label, false_label, end_label

    def compile_if(self, true_label, false_label, end_label):
        self.ctx.emit_label(true_label)

    def compile_else(self, false_label, end_label):
        self.ctx.emit("JMP", end_label)
        self.ctx.emit_label(false_label)

    def compile_endif(self, end_label):
        self.ctx.emit_label(end_label)

    def compile_while_start(self, start_label):
        self.ctx.emit_label(start_label)

    def compile_while_condition(self, start_label, true_label, false_label, end_label):
        self.ctx.emit_label(true_label)

    def compile_while_end(self, start_label, end_label):
        self.ctx.emit("JMP", start_label)
        self.ctx.emit_label(end_label)

    def compile_boolop(self, boolop_node, expr_visitor):
        op_type = type(boolop_node.op).__name__
        true_label = self.ctx.new_label("bool_true")
        false_label = self.ctx.new_label("bool_false")
        end_label = self.ctx.new_label("bool_end")

        if op_type == "And":
            self._compile_and_chain(boolop_node.values, true_label, false_label, expr_visitor)
        elif op_type == "Or":
            self._compile_or_chain(boolop_node.values, true_label, false_label, expr_visitor)
        else:
            raise NotImplementedError(f"BoolOp '{op_type}' not supported")

        return true_label, false_label, end_label

    def _compile_and_chain(self, values, true_label, false_label, expr_visitor):
        for i, value in enumerate(values):
            next_test = self.ctx.new_label("and_test")
            result = expr_visitor.visit(value)
            left_reg, right_reg, op = result
            jump_op = self._jump_for_op(op)
            self.ctx.emit(jump_op, left_reg, right_reg, next_test)
            self.ctx.emit("JMP", false_label)
            self.ctx.emit_label(next_test)
        self.ctx.emit("JMP", true_label)

    def _compile_or_chain(self, values, true_label, false_label, expr_visitor):
        for i, value in enumerate(values):
            next_test = self.ctx.new_label("or_test")
            result = expr_visitor.visit(value)
            left_reg, right_reg, op = result
            jump_op = self._jump_for_op(op)
            self.ctx.emit(jump_op, left_reg, right_reg, true_label)
            self.ctx.emit("JMP", next_test)
            self.ctx.emit_label(next_test)
        self.ctx.emit("JMP", false_label)

    def _jump_for_op(self, op):
        if isinstance(op, str):
            op_name = op
        else:
            op_name = type(op).__name__
        jump_map = {"Gt": "JGT", "Lt": "JLT", "Eq": "JEQ", "NotEq": "JNE"}
        jump_op = jump_map.get(op_name)
        if jump_op is None:
            raise NotImplementedError(f"Comparison '{op_name}' not supported")
        return jump_op

    def compile_for_range(self, counter_reg, start_val, end_val, expr_visitor, visit_body, has_else=False, visit_else=None):
        if end_val is None:
            raise NotImplementedError("range() requires at least an end value")

        # Gerar ID único (vamos usar label_counter do ctx que sempre cresce)
        uid = self.ctx.label_counter

        if isinstance(start_val, str):
            self.ctx.emit_copy(counter_reg, start_val)
        elif start_val is not None:
            self.ctx.emit("SET", counter_reg, start_val)
        else:
            self.ctx.emit("SET", counter_reg, 0)

        limit_reg = self.ctx.allocate_temp("for_limit")
        if isinstance(end_val, str):
            self.ctx.emit_copy(limit_reg, end_val)
        else:
            self.ctx.emit("SET", limit_reg, end_val)

        start_label = self.ctx.new_label("for_start")
        body_label = self.ctx.new_label("for_body")
        inc_label = self.ctx.new_label("for_inc")
        natural_end_label = self.ctx.new_label("for_natural_end")
        break_label = natural_end_label if not has_else else self.ctx.new_label("for_break")

        self.ctx.emit_label(start_label)
        self.ctx.emit("JLT", counter_reg, limit_reg, body_label)
        self.ctx.emit("JMP", natural_end_label)

        self.ctx.emit_label(body_label)
        
        self.ctx.push_loop(inc_label, break_label)
        visit_body()
        self.ctx.pop_loop()

        self.ctx.emit_label(inc_label)
        inc_reg = self.ctx.allocate_temp("for_inc")
        self.ctx.emit("SET", inc_reg, 1)
        self.ctx.emit("ADD", counter_reg, inc_reg)
        self.ctx.emit("JMP", start_label)
        
        self.ctx.emit_label(natural_end_label)
        if has_else and visit_else:
            visit_else()
            self.ctx.emit_label(break_label)