import ast
import sys

class MyVMCompiler(ast.NodeVisitor):
    def __init__(self):
        self.asm = []
        self.ram_offset = 0
        self.label_counter = 0

    def get_new_label(self, base):
        self.label_counter += 1
        return f"{base}_{self.label_counter}"

    def compile(self, tree):
        self.asm.append("main:")
        self.visit(tree)
        self.asm.append("HALT;")
        return "\n".join(self.asm)

    def visit_FunctionDef(self, node):
        # Verifica se tem o decorator @entry_point ou se chama main
        has_entry_point = any(
            isinstance(d, ast.Name) and d.id == 'entry_point' for d in node.decorator_list
        )
        if has_entry_point or node.name == 'main':
            for stmt in node.body:
                self.visit(stmt)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            func_name = ""
            if isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
            
            if func_name == "print_str":
                arg = node.value.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    s = arg.value
                    # Gera a injeção do Assembly
                    self.asm.append(f'WRITESTR "{s}";')
                    
                    start_addr = self.ram_offset
                    length = len(s)
                    self.ram_offset += length
                    
                    loop_lbl = self.get_new_label("print_loop")
                    end_lbl = self.get_new_label("print_end")
                    
                    self.asm.append(f"SET A, {start_addr};")
                    self.asm.append(f"SET B, {length};")
                    self.asm.append(f"SET E, 1;")
                    
                    self.asm.append(f"{loop_lbl}:")
                    self.asm.append(f"LOAD C, A;")
                    self.asm.append(f"PRINTCHAR C;")
                    self.asm.append(f"ADD A, E;")
                    self.asm.append(f"SUB B, E;")
                    self.asm.append(f"JZ B, {end_lbl};")
                    self.asm.append(f"JMP {loop_lbl};")
                    
                    self.asm.append(f"{end_lbl}:")
                    self.asm.append(f"PRINTCHAR 10; // Pula linha")
                    
        self.generic_visit(node)

def main():
    input_file = "test_codes/pyasm/main.py"
    output_file = "test_codes/pyasm/output.asm"
    
    with open(input_file, "r", encoding="utf-8") as f:
        code = f.read()
    
    tree = ast.parse(code)
    compiler = MyVMCompiler()
    asm_code = compiler.compile(tree)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(asm_code)
        
    print(f"Sucesso! Código Python compilado em: {output_file}")

if __name__ == "__main__":
    main()
