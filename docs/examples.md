# Exemplos de Programas

Programas exemplo que demonstram os recursos do compilador.

## Hello World

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    print_str("Hello World")
```

Saída: `Hello World`

## Variáveis e Expressões

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    a = 10
    b = 5
    c = a + b
    d = a - b
    e = a * b
    f = a / b
    print_str("OK")
```

Saída: `OK`

## Condicional If/Else

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 10
    if x > 5:
        print_str("MAIOR")
    else:
        print_str("MENOR")
```

Saída: `MAIOR`

## Loop While (Contador)

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    count = 0
    while count < 5:
        count += 1
    print_str("DONE")
```

Saída: `DONE`

## Fatorial

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    n = 5
    result = 1
    while n > 1:
        result = result * n
        n = n - 1
    print_str("OK")
```

Calcula 5! = 120. Saída: `OK`

## Comparação de Igualdade

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 42
    if x == 42:
        print_str("EQUAL")
    else:
        print_str("DIFF")
```

Saída: `EQUAL`

## Comparação de Diferença

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 10
    if x != 5:
        print_str("DIFFERENT")
```

Saída: `DIFFERENT`

## Loop com Condição Complexa

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    n = 10
    while n > 0:
        n = n - 1
    if n == 0:
        print_str("ZERO")
```

Saída: `ZERO`

## Múltiplas Condições

```python
from myvm_lib import entry_point, print_str

@entry_point
def main():
    x = 15
    if x > 20:
        print_str("BIG")
    else:
        if x > 10:
            print_str("MEDIUM")
        else:
            print_str("SMALL")
```

Saída: `MEDIUM`

## Como Executar

```bash
# Compilar
python3 vm-compiler/main.py exemplo.py exemplo.asm

# Executar na VM
cargo run -- exemplo.asm
```