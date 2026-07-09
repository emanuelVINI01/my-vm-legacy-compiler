import ast
from .base import BaseVisitor


class FunctionVisitor(BaseVisitor):
    def __init__(self, ctx):
        super().__init__(ctx)
        from .statements import StatementVisitor
        self.stmt_visitor = StatementVisitor(ctx)

    def visit_modules(self, modules):
        ordered = self._topological_sort(modules)
        all_pending_funcs = []

        for module_name, mod_path, tree in ordered:
            self.ctx.current_module = module_name

            if module_name == "main":
                funcs = self._process_module(module_name, tree, is_entry=True)
                all_pending_funcs.extend(funcs)
            else:
                self._register_module_imports(module_name, tree)
                funcs = self._process_module(module_name, tree, is_entry=False)
                all_pending_funcs.extend(funcs)

        self.ctx.emit("HALT")

        for func_node, mod_name in all_pending_funcs:
            self._compile_function_body(func_node, mod_name)

    def _topological_sort(self, modules):
        module_set = {name for name, _, _ in modules}
        in_degree = {name: 0 for name in module_set}
        deps = {}

        for name, path, tree in modules:
            mod_deps = self._extract_deps(tree)
            deps[name] = mod_deps
            for dep in mod_deps:
                if dep in in_degree:
                    in_degree[name] += 1

        queue = [n for n, d in in_degree.items() if d == 0]
        order = []

        while queue:
            current = queue.pop(0)
            matches = [(n, p, t) for n, p, t in modules if n == current]
            if matches:
                order.append(matches[0])
            for name in module_set:
                if current in deps.get(name, set()):
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)

        return order

    def _extract_deps(self, tree):
        deps = set()
        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    if alias.name not in {"myvm_lib"}:
                        deps.add(alias.name)
            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module and stmt.module not in {"myvm_lib"}:
                    deps.add(stmt.module)
        return deps

    def _register_module_imports(self, module_name, tree):
        body = getattr(tree, 'body', tree)
        for stmt in body:
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    if alias.name not in {"myvm_lib"}:
                        self.ctx.imported_modules.add(alias.name)
            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module and stmt.module not in {"myvm_lib"}:
                    self.ctx.imported_modules.add(stmt.module)
                    for alias in stmt.names:
                        if alias.name == "*":
                            continue
                        mangled = self.ctx.mangle_name(stmt.module, alias.name)
                        local = alias.asname if alias.asname else alias.name
                        self.ctx.module_aliases[(module_name, local)] = mangled

    def _process_module(self, module_name, tree, is_entry=False):
        body = getattr(tree, 'body', tree)
        main_body = None
        pending_funcs = []

        for stmt in body:
            if isinstance(stmt, ast.FunctionDef):
                has_entry = any(
                    isinstance(d, ast.Name) and d.id == "entry_point"
                    for d in stmt.decorator_list
                )
                mangled = self.ctx.mangle_name(module_name, stmt.name)

                if is_entry and (has_entry or stmt.name == "main"):
                    main_body = stmt.body
                else:
                    params = [arg.arg for arg in stmt.args.args]
                    self.ctx.register_function(mangled, params, stmt)
                    pending_funcs.append((stmt, module_name))

            elif isinstance(stmt, ast.Import):
                if is_entry:
                    self._register_module_imports(module_name, tree)

            elif isinstance(stmt, ast.ImportFrom):
                if is_entry:
                    self._register_module_imports(module_name, tree)

            elif is_entry and not isinstance(stmt, ast.FunctionDef):
                pass

        if is_entry:
            if main_body is None:
                raise RuntimeError(
                    "No main function found. Use @entry_point or define main()."
                )
            for stmt in main_body:
                self.stmt_visitor.visit(stmt)

        return pending_funcs

    def _compile_function_body(self, func_node, module_name):
        mangled = self.ctx.mangle_name(module_name, func_node.name)
        prev_module = self.ctx.current_module
        self.ctx.current_module = module_name

        func_info = self.ctx.get_function(mangled)
        params = func_info["params"]
        arg_regs = ["A", "B", "C", "D", "E"]

        self.ctx.emit_label(mangled)

        for i, param_name in enumerate(params):
            reg = arg_regs[i] if i < len(arg_regs) else None
            if reg:
                self.ctx.variables[param_name] = {"reg": reg, "type": "int", "len": 0}

        for stmt in func_node.body:
            self.stmt_visitor.visit(stmt)

        self.ctx.emit("JMP", "Z")
        self.ctx.current_module = prev_module