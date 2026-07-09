# Arquitetura do VM Compiler

## Visão Geral

O **VM Compiler** compila um subconjunto de Python para assembly da VM personalizada (`my-vm`).
Ele usa a AST do Python (`ast.parse`) para analisar o código fonte e gera instruções assembly
que são executadas pela VM.

## Fluxo de Compilação

```
Código Python (.py)
        |
        v
  ast.parse()
        |
        v
  Compiler (Singleton)
        |
        v
  FunctionVisitor  -->  StatementVisitor  -->  ExpressionVisitor
        |                    |                       |
        v                    v                       v
  CompilationContext  +  CodeEmitter  +  CodegenPatterns
        |                    |                       |
        +--------------------+-----------------------+
        |
        v
  Assembly (.asm)
        |
        v
  VM Rust (my-vm)
```

## Estrutura de Diretórios

```
vm-compiler/
├── main.py              # CLI entry point
├── myvm_lib.py          # Type stubs para a linguagem
├── compiler/
│   ├── compiler.py      # Compiler (Singleton - orquestrador)
│   ├── context.py       # CompilationContext (estado: registradores, labels, RAM)
│   ├── emitter.py       # CodeEmitter (monta texto assembly)
│   ├── patterns.py      # CodegenPatterns (padrões: if/else, while, comparações)
│   └── visitors/
│       ├── base.py      # BaseVisitor (helpers comuns)
│       ├── expressions.py # ExpressionVisitor (BinOp, Compare, Name, Constant)
│       ├── statements.py  # StatementVisitor (If, While, Assign, AugAssign, Expr)
│       └── functions.py   # FunctionVisitor (FunctionDef + entry_point)
├── tests/               # Testes unitários e de integração
└── docs/                # Documentação
```

## Princípios de Design (SOLID)

| Princípio | Aplicação |
|-----------|-----------|
| **S**ingle Responsibility | Cada módulo tem uma única responsabilidade: emitter só gera texto, context só gerencia estado, patterns só gera padrões de código |
| **O**pen/Closed | Visitors podem ser estendidos com novos métodos `visit_*` sem modificar existentes |
| **L**iskov Substitution | BaseVisitor define a interface; ExpressionVisitor e StatementVisitor estendem sem quebrar |
| **I**nterface Segregation | Cada visitor expõe apenas os métodos de visita relevantes para seu domínio |
| **D**ependency Inversion | Módulos de alto nível (Compiler) dependem de abstrações (Context), não de detalhes |

## Padrão Singleton

A classe `Compiler` implementa o padrão **Singleton**:
- Apenas uma instância existe durante a compilação
- `Compiler.reset_instance()` permite reinicializar para testes
- Garante que o estado global (contexto) seja consistente

## Mapeamento de Variáveis

| Recurso | Implementação |
|---------|---------------|
| Registradores | 24 disponíveis (A-X). Y é scratch, Z é reservado para CALL |
| Alocação | First-fit sequencial. Variáveis com mesmo nome reusam o mesmo registrador |
| Temporários | Registradores `_const_*`, `_cmp_*`, `_expr_*`, `_prlen` para cálculos intermediários |

## Codegen de Comparações

| Python | Assembly VM |
|--------|-------------|
| `a > b` | `JGT reg_a, reg_b, true_label` |
| `a < b` | `JLT reg_a, reg_b, true_label` |
| `a == b` | `JEQ reg_a, reg_b, true_label` |
| `a != b` | `JNE reg_a, reg_b, true_label` |

## Codegen de Controle de Fluxo

### If/Else
```asm
JGT A B if_true     ; condição
JMP if_false        ; senão
if_true:
    ; corpo do if
    JMP if_end
if_false:
    ; corpo do else
if_end:
```

### While
```asm
while_start:
    ; avalia condição
    JLT A B while_body   ; se verdadeira
    JMP while_end        ; senão sai
while_body:
    ; corpo do loop
    JMP while_start
while_end:
```

## Codegen de print_str

Usa `WRITESTR` para injetar a string na RAM e `GETLASTADDR` para calcular
o endereço inicial em tempo de execução, garantindo funcionamento correto
mesmo dentro de branches condicionais.