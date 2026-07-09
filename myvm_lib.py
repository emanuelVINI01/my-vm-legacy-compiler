# myvm_lib.py
# Stubs para a IDE entender a sintaxe, mas que serão interceptados pelo nosso compilador AST.

def entry_point(func):
    """Marcador para a função principal que a VM vai rodar."""
    return func

def print_str(s: str):
    """Escreve uma string na memória da VM e itera printando cada caractere."""
    pass
