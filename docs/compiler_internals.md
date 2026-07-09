# Internals do Compilador

Este documento explica como o compilador funciona internamente, para desenvolvedores
que queiram estender ou modificar o compilador.

## Pipeline de Compilação

### 1. Parsing (ast.parse)

O código Python é analisado usando o módulo `ast` da biblioteca padrão do Python.
Isso produz uma árvore sintática abstrata (AST).

```python
import ast
tree = ast.parse('x = 5 + 3')
# tree.body[0] é um nó ast.Assign
```

### 2. Visitor Pattern (NodeVisitor)

O compilador usa o padrão **Visitor** do módulo `ast.NodeVisitor`.
Cada nó da AST é visitado por um método `visit_<NomeDoNó>`.

Hierarquia de visitors:
```
BaseVisitor (ast.NodeVisitor)
├── ExpressionVisitor (BinOp, Compare, Name, Constant)
├── StatementVisitor (Assign, AugAssign, If, While, Expr)
└── FunctionVisitor (FunctionDef)
```

### 3. CompilationContext

Gerencia o estado global da compilação:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `variables` | `Dict[str, str]` | Mapeia nome de variável → registrador |
| `next_register` | `int` | Próximo registrador livre (índice) |
| `label_counter` | `int` | Contador para gerar labels únicos |
| `emitter` | `CodeEmitter` | Referência para o emissor de código |

**Alocação de Registradores:**
- Primeira variável → A, segunda → B, etc.
- Pula Y (scratch) e Z (return do CALL)
- Variáveis com mesmo nome reusam o registrador
- Temporários usam nomes como `_const_1`, `_cmp_val_2`

### 4. CodeEmitter

Transforma operações em strings assembly:

```python
emitter.emit("SET", "A", 42)       # → "SET A 42;"
emitter.emit_label("loop")          # → "loop:"
emitter.emit_comment("início")      # → "// início"
```

### 5. CodegenPatterns

Gera padrões de código de alto nível para construções de linguagem:

**Comparação:**
```python
def compile_comparison(self, op, left_reg, right_reg):
    # Emite: JGT/JLT/JEQ/JNE left right true_label
    #         JMP false_label
    # Retorna: (true_label, false_label, end_label)
```

**If/Else:**
```python
def compile_if(self, true_label, false_label, end_label):
    # Emite true_label:

def compile_else(self, false_label, end_label):
    # Emite: JMP end_label
    #        false_label:

def compile_endif(self, end_label):
    # Emite end_label:
```

### 6. Fluxo de Compilação Detalhado

#### Variáveis (`x = 5`)
```
visit_Assign → allocate_register("x") = "A" → emit("SET", "A", 5)
```

#### Expressões (`y = x + 3`)
```
visit_Assign → visit_BinOp →
  visit_Name("x") → get_register("x") = "A"
  visit_Constant(3) → allocate_register("_const_1") = "B"
                       emit("SET", "B", 3)
  allocate_register("_expr_temp") = "C"
  emit("SET", "C", "A")       ; copia x
  emit("ADD", "C", "B")       ; C = A + B
  return "C"
→ emit("SET", "D", "C")       ; y = resultado
```

#### If/Else (`if x > 5: ... else: ...`)
```
visit_If → visit_Compare →
  visit_Name("x") → "A"
  visit_Constant(5) → allocate("_cmp_val") = "B", emit("SET", "B", 5)
  return ("A", "B", Gt)

compile_comparison(Gt, "A", "B") →
  labels: true="cmp_true_1", false="cmp_false_2"
  emit("JGT", "A", "B", "cmp_true_1")
  emit("JMP", "cmp_false_2")

compile_if → emit_label("cmp_true_1")
  // visita corpo do if

compile_else → emit("JMP", "cmp_end_3"), emit_label("cmp_false_2")
  // visita corpo do else

compile_endif → emit_label("cmp_end_3")
```

#### While (`while x < 10: ...`)
```
visit_While →
  start_label = "while_start_1"

  visit_Compare → ("A", register_of_10, Lt)

  compile_comparison(Lt, "A", reg, ...) →
    emit("JLT", "A", reg, "cmp_true_X")
    emit("JMP", "cmp_false_Y")

  emit_label("cmp_true_X")
  // visita corpo do loop
  emit("JMP", "while_start_1")
  emit_label("cmp_false_Y")
```

## Como Adicionar Novos Recursos

### Adicionar um novo operador de comparação

1. Adicione o opcode na VM Rust (`src/opcodes.rs`)
2. Adicione parsing em `src/parser/mod.rs`
3. Implemente execução em `src/machine/executor.rs`
4. Adicione o mapeamento em `compiler/patterns.py` no dicionário `jump_map`
5. Adicione o nó AST correspondente no `visit_Compare`

### Adicionar um novo statement (ex: for loop)

1. Crie `visit_For` no `StatementVisitor`
2. Implemente a tradução para assembly usando os opcodes existentes
3. Se necessário, adicione padrões em `CodegenPatterns`

### Adicionar suporte a strings como valores

1. Altere `visit_Assign` para detectar `ast.Constant(str)`
2. Use `WRITESTR` para armazenar a string na RAM
3. Use `GETLASTADDR` para rastrear o endereço
4. Armazene o endereço no registrador da variável