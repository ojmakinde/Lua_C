from MIPS_Emitter import Emitter
from Lua import Lua

def main():
    return

if __name__ == "__main__":
    instance = Lua()
    ast, symbol_table = instance.export_ast(), instance.symbol_table
    emitter = Emitter(ast, symbol_table)
    print(emitter.asm_text)