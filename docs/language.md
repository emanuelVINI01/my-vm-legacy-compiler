# Guia da Linguagem Suportada

O VM Compiler compila um subconjunto de Python. Abaixo está a sintaxe suportada.

## Estrutura Básica

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    # seu código aqui
```

- `@entry_point` é obrigatório para marcar a função principal
- A função deve se chamar `main` (ou ter o decorator `@entry_point`)
- Apenas uma função é compilada

## Variáveis

```python
x = 42          # atribuição de constante
y = x           # cópia de variável
z = x + y       # expressão aritmética
count = 0       # inicialização
```

- Nomes de variáveis podem conter letras, números e underscore
- Tipos: apenas inteiros (`u32` internamente)

## Operações Aritméticas

```python
a = 10 + 5      # adição
b = 10 - 3      # subtração
c = 4 * 5       # multiplicação
d = 20 / 4      # divisão (inteira)

x += 1          # atribuição aumentada
x -= 2
x *= 3
```

## Operadores de Comparação

| Operador | Significado |
|----------|-------------|
| `>` | Maior que |
| `<` | Menor que |
| `==` | Igual a |
| `!=` | Diferente de |

## Condicionais (If/Else)

```python
if x > 10:
    y = 1
else:
    y = 0
```

```python
if a == b:
    print_str("Iguais")
```

- Suporta `if` simples e `if/else`
- Condições devem ser comparações simples (não suporta `and`/`or`)

## Loops (While)

```python
count = 0
while count < 10:
    count += 1
```

```python
while n > 1:
    n = n - 1
```

- Condições do while devem ser comparações simples
- Não suporta `break` ou `continue`

## Função print_str

```python
print_str("Hello World")
```

- Imprime uma string literal na saída padrão
- Apenas strings literais são suportadas (não variáveis)
- Sempre adiciona uma quebra de linha ao final

## Limitações

- Apenas 24 variáveis simultâneas (registradores A-X)
- Não suporta funções definidas pelo usuário (apenas `main`)
- Não suporta listas, dicionários, strings como valores
- Não suporta `and`, `or`, `not`
- Não suporta `for`, `break`, `continue`
- Não suporta chamadas aninhadas de função
- Valores são inteiros sem sinal de 32 bits (`u32`)

## Exemplo Completo

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    n = 10
    result = 1

    while n > 1:
        result = result * n
        n = n - 1

    if result == 3628800:
        print_str("OK")
    else:
        print_str("FAIL")
```