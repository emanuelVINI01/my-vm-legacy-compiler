REGISTERS = [chr(ord('A') + i) for i in range(26)]
SCRATCH_REGISTER = "Y"
RETURN_REGISTER = "Z"


class CompilationContext:
    def __init__(self):
        self.emitter = None
        self.variables = {}
        self.next_register = 0
        self.label_counter = 0
        self.ram_offset = 0
        self.function_registry = {}
        self.array_bases = {}
        self.loop_stack = []
        self.module_aliases = {}
        self.imported_modules = set()
        self.current_module = "main"
        self.active_temps = set()
        self.free_temps = []

    def push_loop(self, continue_label, break_label):
        self.loop_stack.append((continue_label, break_label))

    def pop_loop(self):
        self.loop_stack.pop()

    def current_loop(self):
        if not self.loop_stack:
            raise Exception("Comando break ou continue foi usado fora de um loop!")
        return self.loop_stack[-1]

    def set_emitter(self, emitter):
        self.emitter = emitter

    def allocate_register(self, var_name, var_type="int", length=0):
        if var_name in self.variables:
            return self.variables[var_name]["reg"]
        reg = self._next_free_register()
        self.variables[var_name] = {"reg": reg, "type": var_type, "len": length}
        return reg

    def allocate_temp(self, tag=""):
        if self.free_temps:
            reg = self.free_temps.pop(0)
            self.active_temps.add(reg)
            return reg
        reg = self._next_temp_register()
        self.active_temps.add(reg)
        return reg

    def free_temp(self, reg):
        self.active_temps.discard(reg)
        if reg not in self.free_temps:
            self.free_temps.append(reg)

    def free_all_temps(self):
        for reg in list(self.active_temps):
            self.active_temps.discard(reg)
            if reg not in self.free_temps:
                self.free_temps.append(reg)

    def _next_temp_register(self):
        skip = {SCRATCH_REGISTER, RETURN_REGISTER}
        used = {info["reg"] for info in self.variables.values()}
        used.update(self.active_temps)
        for reg in REGISTERS:
            if reg not in skip and reg not in used:
                return reg
        raise RuntimeError("No free registers available")

    def get_register(self, var_name):
        if var_name not in self.variables:
            raise NameError(f"Variable '{var_name}' is not defined")
        return self.variables[var_name]["reg"]

    def get_var_info(self, var_name):
        if var_name not in self.variables:
            raise NameError(f"Variable '{var_name}' is not defined")
        return self.variables[var_name]

    def _next_free_register(self):
        skip = {SCRATCH_REGISTER, RETURN_REGISTER}
        used = {info["reg"] for info in self.variables.values()}
        used.update(self.active_temps)
        used.update(self.free_temps)
        for reg in REGISTERS:
            if reg not in skip and reg not in used:
                return reg
        raise RuntimeError("No free registers available")

    def register_function(self, name, params, node):
        label = name
        self.function_registry[name] = {
            "label": label,
            "params": params,
            "node": node,
        }

    def get_function(self, name):
        if name not in self.function_registry:
            raise NameError(f"Function '{name}' is not defined")
        return self.function_registry[name]

    def is_array(self, var_name):
        return var_name in self.array_bases

    def register_array(self, var_name):
        self.array_bases[var_name] = True

    def mangle_name(self, module_name, func_name):
        if module_name == "main" or module_name == "__main__":
            return func_name
        return f"{module_name}_{func_name}"

    def resolve_call_target(self, func_expr_node):
        if isinstance(func_expr_node, str):
            local_name = func_expr_node
            alias_key = (self.current_module, local_name)
            if alias_key in self.module_aliases:
                return self.module_aliases[alias_key]
            if local_name in self.function_registry:
                return local_name
            mangled = self.mangle_name(self.current_module, local_name)
            if mangled in self.function_registry:
                return mangled
            return local_name

        import ast
        if isinstance(func_expr_node, ast.Name):
            return self.resolve_call_target(func_expr_node.id)
        elif isinstance(func_expr_node, ast.Attribute):
            module_name = func_expr_node.value.id
            method = func_expr_node.attr
            mangled = self.mangle_name(module_name, method)
            if mangled in self.function_registry:
                return mangled
            return "{}_{}".format(module_name, method)
        else:
            return None

    def emit_copy(self, dest_reg, src_reg):
        if dest_reg == src_reg:
            return
        self.emit("SET", dest_reg, 0)
        self.emit("ADD", dest_reg, src_reg)

    def new_label(self, prefix):
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def emit(self, opcode, *operands):
        self.emitter.emit(opcode, *operands)

    def emit_label(self, name):
        self.emitter.emit_label(name)

    def emit_comment(self, text):
        self.emitter.emit_comment(text)