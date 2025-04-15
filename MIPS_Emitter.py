from AST import AST

class Emitter:
    def __init__(self, ast, symbol_table=None) -> None:
        self.ast = ast
        self.symbol_table = symbol_table
        self.string_counter = 0  # Counter for unique string labels
        self.string_literals = {} 
        self.asm_data_section = ".data\n"
        self.asm_text_section = ""
        self.emit_ast()

    def get_string_symbol(self, string_value):
        """Get or create a symbol table entry for a string literal"""
        # Check if this string already exists
        if string_value in self.string_literals:
            return self.string_literals[string_value]
        
        # Create a new symbol for this string
        symbol = f"str_{self.string_counter}"
        self.string_counter += 1
        self.string_literals[string_value] = symbol
        
        return symbol

    def mips32_macros(self):
        return """
#  CSC486 Macros in MIPS 32 Assembly
#
#  Author: Oluwagbayi J. Makinde
# Created: 2025-03-15
# Purpose: Implementation of Lua emitter using boilerplate from Prof. Wilborne
#  Course: 2025 Spring CSC486
#   
#   Milestone 1: Completed all binop operations, implemented passing file path as cmd arg
#                float recognition, and print keyword in Lua (which is print())
#
#   Milestone 2: Implemented string printing.
#
#
# History:
#           2024-01-28, DMW, created

           .text                       # time to assemble!

           .macro prt_lf               # print a linefeed
           li      $a0, 10             # linefeed character
           li      $v0, 11             # print a character syscall
           syscall                     # print the character
           .end_macro

           .macro prt_chr($chr)        # print any character
           li      $a0, $chr           # $a0 = the character in $chr
           li      $v0, 11             # print a character syscall #
           syscall                     # print the character
           .end_macro

#       push a register with word onto the stack
           .macro  pushw($reg)
           sub     $sp, $sp, 4     # allocate space on stack
           sw      $reg, 4($sp)    # push the word on the stack
           .end_macro

#       pull a word off the stack into a register
           .macro popw($reg)
           lw      $reg, 4($sp)    # load the word from the stack
           add     $sp, $sp, 4     # free space on stack
           .end_macro

#       insert the exit program system call wherever used
           .macro exit_prog
           li  $v0, 10             # specify exit system call
           syscall                 # exit the program
           .end_macro"""

    def emit_ast(self) -> None:

        def emit_children(children: []) -> None:
            for child in children:
                emit(child)

        def out_asm_data(line:str = None) -> None:
            if line is not None:
                self.asm_data_section += f"{line} \n"

        def out_asm_text(line: str = None) -> None:
            if line is not None:
                self.asm_text_section += f"{line} \n"

        def hr() -> None:
            out_asm_text(" # -------------------------------------------------------------------------------------")

        def print_lf() -> None:
            out_asm_text("li $v0, 11")  # print character syscall number
            out_asm_text("li $a0, 10")  # linefeed character
            out_asm_text("syscall")

        def store_string(data_label: str, out_str: str) -> None:
            if '"' in out_str:
                # if true, write out string as bytes when it has nested " characters
                out_bytes = ""
                for ch in out_str:
                    out_bytes = out_bytes + str(ord(ch)) + " "
                out_bytes = out_bytes + "0 # " + out_str
                out_asm_data(data_label + ": .byte " + out_bytes)
            else:
                out_asm_data(data_label + ": .asciiz \"" + out_str + '"')

        def emit(node: AST) -> None:
            match node.name:
                case "program":
                    out_asm_text("# program node")
                    if len(self.symbol_table) > 0:
                        for symbol in self.symbol_table:
                            out_asm_data("{}: .word 0".format(self.symbol_table[symbol]))
                        hr()
                    out_asm_text(".text")
                    out_asm_text(self.mips32_macros())
                    hr()
                    emit_children(node.children)
                    hr()
                    out_asm_text("exit_prog")
                case "opt_stmts": emit_children(node.children)
                case "stmt_list": emit_children(node.children)
                case "nop": return
                case "parentheses":
                    out_asm_text("# parentheses node")
                    emit_children(node.children)
                    out_asm_text("# end of parentheses node")
                case "assignment":
                    out_asm_text("# assignment to: {}".format(node.value['symbol']))
                    emit_children(node.children)
                    out_asm_text("popw($t7)")  # get the value of the right hand expression from CPU stack
                    out_asm_text("la $t6, {}".format(node.value['symbol']))  # get address of storage location
                    out_asm_text("sw $t7, 0($t6)")  # put value of rhs into storage location
                    out_asm_text("# end of assignment")
                case "string":
                    out_asm_text("#-- string node")
                    string_label = self.get_string_symbol(node.value)
                    store_string(string_label, node.value)
                    out_asm_text(f"la $t7, {string_label}")
                    out_asm_text("pushw($t7)")
                    out_asm_text("#-- end of string node")
                case "print":
                    out_asm_text("#-- print node")
                    if not node.children:
                        out_asm_text("# Warning: print with no argument")
                        return
                    emit_children(node.children)
                    if node.children[0].name == "ID":   # if id, then it could hold any data type
                        out_asm_text("#-- printing variable and verifying type")
                        out_asm_text("popw($a0)")
                        out_asm_text("li $v0, 4")
                    if node.children[0].name == "string":
                        out_asm_text("#-- printing string")
                        out_asm_text("popw($a0)")
                        out_asm_text("li $v0, 4")
                    else:
                        out_asm_text("#-- printing integer")
                        out_asm_text("popw($a0)") 
                        out_asm_text("li $v0, 1")

                    out_asm_text("syscall")
                    print_lf()
                    out_asm_text("#-- end of print node")
                case "number":
                    out_asm_text("#-- number node")
                    out_asm_text("li $t7, {}".format(node.value))
                    out_asm_text("pushw($t7)")
                    out_asm_text("#-- end of number node")
                case "unary":
                    out_asm_text("# unary node: {}".format(node.value))
                    emit_children(node.children)
                    out_asm_text("popw($t7)")
                    out_asm_text("neg $t7, $t7")
                    # should i catch the case where you have like -abc?
                    out_asm_text("pushw($t7)") 
                    out_asm_text("# end of unary node")
                case "binop":
                    out_asm_text("# binop node: {}".format(node.value))
                    emit_children(node.children)  # should leave two values on the CPU stack
                    out_asm_text("popw($t7)")  # gets the right hand side
                    out_asm_text("popw($t6)")  # gets the left hand side
                    match node.value:
                        case "+": out_asm_text("add $t7, $t6, $t7")  # $t7 = $t6 + $t7
                        case "-": out_asm_text("sub $t7, $t6, $t7")
                        case "*": out_asm_text("mulu $t7, $t6, $t7")
                        case "/": out_asm_text("divu $t7, $t6, $t7")
                    out_asm_text("pushw($t7)")  # put the result of the binop on the CPU stack
                    out_asm_text("# end of binop node")
                case "ID":
                    # get the address of the symbol stored in the ID node
                    out_asm_text("# look up ID: {}".format(node.value['id']))
                    out_asm_text("la $t7, {}".format(self.symbol_table[node.value['id']]))
                    out_asm_text("lw $t7, 0($t7)")  # get the value stored at address $t7 into $t7
                    out_asm_text("pushw($t7)")  # push the value on to the stack
                    out_asm_text("# end of look up ID")
                case _:
                    print(node.name)
                    # raise SyntaxWarning("Emitter error: AST node unknown: {}".format(node.name))

        # generate the assembly code
        emit(self.ast)

    def export_asm(self):
        f = open("asm_output.txt", "w")
        print(self.asm_data_section)
        print(self.asm_text_section)
        f.write(self.asm_data_section + "\n" + self.asm_text_section)
        f.close()