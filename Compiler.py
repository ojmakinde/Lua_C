from MIPS_Emitter import Emitter
from Lua import Lua
import sys

def main():
    return

if __name__ == "__main__":
    file_path, text_stream = None, None
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    if file_path:
        with open(file_path, 'r') as file:
            text_stream = file.read()
    instance = Lua()
    ast, symbol_table = instance.export_ast(text_stream), instance.symbol_table
    emitter = Emitter(ast, symbol_table)
    emitter.export_asm()