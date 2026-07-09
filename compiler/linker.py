import ast
import os


class Linker:
    BUILTINS = {"myvm_lib"}

    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.parsed = {}
        self.processing = set()

    def resolve(self, entry_path):
        abs_path = os.path.abspath(entry_path)
        entry_abs = abs_path
        self._discover(abs_path)
        order = self._topological_sort()
        result = []
        for mod_name, mod_path in order:
            tree = self.parsed[mod_path]
            if mod_path == entry_abs:
                result.append(("main", mod_path, tree))
            else:
                result.append((mod_name, mod_path, tree))
        return result

    def _discover(self, abs_path):
        if abs_path in self.parsed:
            return
        if abs_path in self.processing:
            raise RuntimeError(f"Circular import detected: {abs_path}")

        self.processing.add(abs_path)

        with open(abs_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        module_name = self._module_name(abs_path)
        self.parsed[abs_path] = tree

        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    if alias.name not in self.BUILTINS:
                        dep_path = self._resolve_path(alias.name, abs_path)
                        if dep_path:
                            self._discover(dep_path)

            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module and stmt.module not in self.BUILTINS:
                    dep_path = self._resolve_path(stmt.module, abs_path)
                    if dep_path:
                        self._discover(dep_path)

        self.processing.discard(abs_path)

    def _topological_sort(self):
        in_degree = {p: 0 for p in self.parsed}
        deps_map = {}

        for mod_path in self.parsed:
            deps = self._extract_deps(mod_path, self.parsed[mod_path])
            deps_map[mod_path] = deps
            for dep_path in deps:
                if dep_path in in_degree:
                    in_degree[mod_path] += 1

        queue = [p for p, d in in_degree.items() if d == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append((self._module_name(current), current))
            for mod_path in self.parsed:
                if current in deps_map.get(mod_path, []):
                    in_degree[mod_path] -= 1
                    if in_degree[mod_path] == 0:
                        queue.append(mod_path)

        if len(order) != len(self.parsed):
            raise RuntimeError("Circular dependency detected — topological sort failed")

        return order

    def _extract_deps(self, mod_path, tree):
        deps = set()
        for stmt in ast.walk(tree):
            if isinstance(stmt, ast.Import):
                for alias in stmt.names:
                    if alias.name not in self.BUILTINS:
                        dep = self._resolve_path(alias.name, mod_path)
                        if dep:
                            deps.add(dep)
            elif isinstance(stmt, ast.ImportFrom):
                if stmt.module and stmt.module not in self.BUILTINS:
                    dep = self._resolve_path(stmt.module, mod_path)
                    if dep:
                        deps.add(dep)
        return deps

    def _resolve_path(self, module_name, origin_path):
        origin_dir = os.path.dirname(origin_path)
        candidate = os.path.join(origin_dir, f"{module_name}.py")
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
        candidate = os.path.join(self.base_dir, f"{module_name}.py")
        if os.path.isfile(candidate):
            return os.path.abspath(candidate)
        return None

    def _module_name(self, abs_path):
        return os.path.splitext(os.path.basename(abs_path))[0]