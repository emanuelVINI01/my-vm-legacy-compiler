class CodeEmitter:
    def __init__(self):
        self.lines = []

    def emit(self, opcode, *operands):
        parts = [opcode]
        for op in operands:
            if isinstance(op, str) and op.startswith('"') and op.endswith('"'):
                parts.append(op)
            else:
                parts.append(str(op))
        self.lines.append(" ".join(parts) + ";")

    def emit_label(self, name):
        self.lines.append(f"{name}: ;")

    def emit_comment(self, text):
        self.lines.append(f"// {text}")

    def emit_raw(self, text):
        self.lines.append(text)

    def get_output(self):
        return "\n".join(self.lines)

    def get_lines(self):
        return list(self.lines)