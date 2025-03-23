from AST import AST

class Emitter:
    def __init__(self, ast, symbol_table=None) -> None:
        self.ast = ast
        self.symbol_table = symbol_table
        self.asm_text = ""
        self.emit_ast()

    def mips32_macros(self):
        return """
#  CSC486 Macros in MIPS 32 Assembly
#
#  Author: Deanna M. Wilborne
# Created: 2024-01-28
# Purpose: Demonstration
#  Course: 2024 Spring CSC486
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
        obj_ctr = 0

        def get_obj_ctr(label) -> str:
            global obj_ctr
            numbered_object = "{}_{:05d}".format(label, obj_ctr)
            obj_ctr = obj_ctr + 1
            return numbered_object

        def emit_children(children: []) -> None:
            for child in children:
                emit(child)

        def out_asm_text(line: str = None) -> None:
            if line is not None:
                self.asm_text = self.asm_text + line + "\n"

        def hr() -> None:
            out_asm_text(" # -------------------------------------------------------------------------------------")

        def emit(node: AST) -> None:
            match node.name:
                case "program":
                    out_asm_text("# program node")
                    if len(self.symbol_table) > 0:
                        out_asm_text(".data")
                        for symbol in self.symbol_table:
                            out_asm_text("{}: .word 0".format(self.symbol_table[symbol]))
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
                case "assignment":
                        out_asm_text("# assignment to: {}".format(node.value['symbol']))
                        emit_children(node.children)
                        out_asm_text("popw($t7)")  # get the value of the right hand expression from CPU stack
                        out_asm_text("la $t6, {}".format(node.value['symbol']))  # get address of storage location
                        out_asm_text("sw $t7, 0($t6)")  # put value of rhs into storage location
                        out_asm_text("# end of assignment")
                # fix this
                # case "print":
                #         out_asm_text("#-- writeln node")
                #         emit_children(node.children)
                #         out_asm_text("popw($t7)")
                #         out_asm_text("move $a0, $t7")
                #         out_asm_text("li $v0, 1")
                #         out_asm_text("syscall")
                #         out_asm_text("prt_lf")
                #         out_asm_text("#-- end of writeln node")
                case "number":
                    out_asm_text("#-- number node")
                    out_asm_text("li $t7, {}".format(node.value))
                    out_asm_text("pushw($t7)")
                    out_asm_text("#-- end of number node")
                case "binop":
                    out_asm_text("# binop node: {}".format(node.value))
                    emit_children(node.children)  # should leave two values on the CPU stack
                    out_asm_text("popw($t7)")  # gets the right hand side
                    out_asm_text("popw($t6)")  # gets the left hand side
                    match node.value:
                        case "+": out_asm_text("add $t7, $t6, $t7")  # $t7 = $t6 + $t7
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