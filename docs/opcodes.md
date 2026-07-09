# Referência de Opcodes da VM

A VM suporta 24 opcodes. Abaixo está a referência completa.

## Registradores

- 26 registradores de propósito geral: `A` a `Z`
- Todos são `u32` (inteiros sem sinal de 32 bits)
- `Z` é usado internamente por `CALL` para armazenar endereço de retorno
- `Y` é reservado pelo compilador como scratch

## Memória RAM

- 1024 células de 32 bits (4 KB)
- Endereçamento de 0 a 1023

## Tabela de Opcodes

### SET — Atribuir valor
```
SET <reg>, <valor>
```
Atribui um valor literal a um registrador.
```asm
SET A, 42        ; A = 42
SET B, 10        ; B = 10
SET C, A         ; C = A (copia valor de A)
```

### ADD — Adição
```
ADD <dest>, <src>
```
Soma o valor de `src` ao valor de `dest`. Resultado em `dest`.
```asm
ADD A, B         ; A = A + B
```

### SUB — Subtração
```
SUB <dest>, <src>
```
Subtrai `src` de `dest`. Resultado em `dest`.
```asm
SUB A, B         ; A = A - B
```

### MUL — Multiplicação
```
MUL <dest>, <src>
```
Multiplica `dest` por `src`. Resultado em `dest`.
```asm
MUL A, B         ; A = A * B
```

### DIV — Divisão
```
DIV <dest>, <src>
```
Divide `dest` por `src` (divisão inteira). Resultado em `dest`.
```asm
DIV A, B         ; A = A / B
```

### LOG — Debug
```
LOG <reg>
```
Imprime o nome e valor de um registrador (para debug).
```asm
LOG A            ; imprime "A: 42"
```

### JMP — Salto Incondicional
```
JMP <label ou registrador>
```
Salta para uma label ou para o endereço armazenado em um registrador.
```asm
JMP loop         ; salta para label "loop"
JMP Z            ; salta para endereço em Z (retorno de CALL)
```

### JZ — Salto se Zero
```
JZ <reg>, <label>
```
Salta para `label` se o valor do registrador for zero.
```asm
JZ A, done       ; se A == 0, salta para done
```

### JGT — Salto se Maior Que
```
JGT <reg>, <valor_ou_reg>, <label>
```
Salta se o valor do registrador for maior que o segundo operando.
```asm
JGT A, B, bigger  ; se A > B, salta
JGT A, 5, bigger  ; se A > 5, salta
```

### JLT — Salto se Menor Que
```
JLT <reg>, <valor_ou_reg>, <label>
```
Salta se o valor do registrador for menor que o segundo operando.
```asm
JLT A, 10, loop   ; se A < 10, salta para loop
```

### JEQ — Salto se Igual (NOVO)
```
JEQ <reg>, <valor_ou_reg>, <label>
```
Salta se o valor do registrador for igual ao segundo operando.
```asm
JEQ A, B, equal   ; se A == B, salta
JEQ A, 42, found  ; se A == 42, salta
```

### JNE — Salto se Diferente (NOVO)
```
JNE <reg>, <valor_ou_reg>, <label>
```
Salta se o valor do registrador for diferente do segundo operando.
```asm
JNE A, B, diff    ; se A != B, salta
JNE A, 0, nonzero ; se A != 0, salta
```

### CALL — Chamada de Sub-rotina
```
CALL <label>
```
Armazena o endereço de retorno em `Z` e salta para `label`.
Para retornar, use `JMP Z`.
```asm
CALL func         ; chama func
; ...continua aqui após JMP Z
func:
    ; corpo da função
    JMP Z         ; retorna
```

### LOAD — Carregar da RAM
```
LOAD <dest>, <endereço>
```
Carrega um valor da RAM para um registrador.
```asm
LOAD A, B         ; A = RAM[B]
LOAD A, 10        ; A = RAM[10]
```

### STORE — Armazenar na RAM
```
STORE <endereço>, <src>
```
Armazena o valor de um registrador na RAM.
```asm
STORE 10, A       ; RAM[10] = A
STORE B, A        ; RAM[B] = A
```

### PRINT — Imprimir Valor
```
PRINT <reg_ou_valor>
```
Imprime um valor com quebra de linha.
```asm
PRINT A           ; imprime valor de A
PRINT 42          ; imprime "42"
```

### PRINTCHAR — Imprimir Caractere
```
PRINTCHAR <reg_ou_valor>
```
Converte o valor para caractere ASCII e imprime (sem quebra de linha).
```asm
PRINTCHAR 65      ; imprime 'A'
PRINTCHAR 10      ; imprime '\n'
```

### WRITESTR — Escrever String na RAM
```
WRITESTR "texto"
```
Escreve cada caractere da string como valor `u32` na RAM sequencialmente.
Usa `last_ram_address` para rastrear a posição.
```asm
WRITESTR "Hello"  ; RAM[0]='H', RAM[1]='e', RAM[2]='l', ...
```

### GETLASTADDR — Obter Último Endereço RAM
```
GETLASTADDR <reg>
```
Armazena o último endereço de RAM escrito pelo `WRITESTR` no registrador.
```asm
GETLASTADDR A     ; A = último endereço escrito
```

### WRITE — Escrever Bloco da RAM
```
WRITE <fd>, <addr_reg>, <length>
```
Escreve `length` bytes da RAM (a partir de `addr_reg`) no file descriptor.
Atualmente apenas `fd=1` (stdout) é suportado.
```asm
WRITE 1, A, 5     ; escreve 5 caracteres da RAM[A] no stdout
```

### HALT — Parar Execução
```
HALT
```
Encerra a execução da VM.
```asm
HALT
```

## Labels

Labels são marcadores de posição no código:
```asm
main:             ; entry point obrigatório
    SET A, 10
loop:             ; label para salto
    SUB A, 1
    JGT A, 0, loop
    HALT
```

## Comentários

```asm
// Isto é um comentário
SET A, 10;  // comentário após instrução
```