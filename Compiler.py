from MIPS_Emitter import Emitter
from Lua import Lua

def main():
    return

if __name__ == "__main__":
    instance = Lua()
    ast = instance.export_ast()
    # Emitter(ast)