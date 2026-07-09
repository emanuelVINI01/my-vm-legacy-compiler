import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from compiler.compiler import Compiler


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m vm-compiler <input.py> [output.asm]")
        print("       python3 vm-compiler/main.py <input.py> [output.asm]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.rsplit(".", 1)[0] + ".asm"

    compiler = Compiler()
    asm_code = compiler.compile_file(input_file)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(asm_code)

    print(f"Compiled '{input_file}' -> '{output_file}'")


if __name__ == "__main__":
    Compiler.reset_instance()
    main()