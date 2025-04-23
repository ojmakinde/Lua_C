from AST import AST

class Emitter:
    def __init__(self, ast, symbol_table=None) -> None:
        self.ast = ast
        self.symbol_table = symbol_table
        self.string_counter = 0  # Counter for unique string labels
        self.label_counter = 0  # For label counting
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
#               - Added the string counter
#               - Improved the functionality of the print case for outputting asm
#
#   Milestone 3: Implemented input reading in Lua syntax
#               - Implemented basic if/else conditional blocks with integer comparisons. Uncertain of my implementation's efficacy on elseif blocks, though.
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
                            symbol_address = self.symbol_table[symbol]["address"]
                            out_asm_data(f"{symbol_address}: .word 0")
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
                    print_type = ""
                    if node.children[0].name == "string":
                        print_type = "string"
                    elif node.children[0].name == "number" or node.children[0].name == "float":
                        print_type = "number"
                    elif node.children[0].name == "ID":
                        # For ID nodes, look up the type in the symbol table
                        symbol_name = node.children[0].value['id']
                        if symbol_name in self.symbol_table:
                            print_type = self.symbol_table[symbol_name]["type"]

                    emit_children(node.children)

                    out_asm_text("popw($a0)")

                    if print_type == "string":
                        out_asm_text("#-- printing string")
                        out_asm_text("li $v0, 4")
                    else:
                        out_asm_text("#-- printing integer/expression")
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
                    # get the address of the symbol stored in the ID node'
                    symbol_id = node.value['id']
                    out_asm_text(f"# look up ID: {symbol_id}")
                    symbol_address = self.symbol_table[symbol_id]["address"]
                    out_asm_text(f"la $t7, {symbol_address}")
                    out_asm_text("lw $t7, 0($t7)")
                    out_asm_text("pushw($t7)")
                    out_asm_text("# end of look up ID")
                case "io_read":
                    print(node)
                    out_asm_text("#-- io.read node")
                    read_type = node.value
                    
                    if read_type == "number":
                        out_asm_text("#-- reading number (*n)")
                        out_asm_text("li $v0, 5")
                        out_asm_text("syscall")
                        out_asm_text("move $t7, $v0")
                    else:  # string
                        out_asm_text("#-- reading string (*l or default)")
                        # Allocate buffer in data section
                        buf_label = f"buf_{len(self.string_literals)}"
                        out_asm_data(f"{buf_label}: .space 256")  # Space for 256 chars
                        
                        out_asm_text(f"la $a0, {buf_label}")  # Load address of buffer
                        out_asm_text("li $a1, 256")
                        out_asm_text("li $v0, 8")
                        out_asm_text("syscall")
                        out_asm_text(f"la $t7, {buf_label}")  # Load string address to $t7
                    
                    out_asm_text("pushw($t7)")
                    out_asm_text("#-- end of io.read node")
                case "comparison":
                    out_asm_text("# comparison node: {}".format(node.value))
                    emit_children(node.children)  # Evaluate both sides
                    out_asm_text("popw($t7)")  # Right operand
                    out_asm_text("popw($t6)")  # Left operand
                    
                    # Generate unique label for this comparison
                    true_label = f"true_{self.label_counter}"
                    end_label = f"end_{self.label_counter}"
                    self.label_counter += 1
                    
                    match node.value:
                        case ">": 
                            out_asm_text(f"bgt $t6, $t7, {true_label}")
                        case "<": 
                            out_asm_text(f"blt $t6, $t7, {true_label}")
                        case ">=": 
                            out_asm_text(f"bge $t6, $t7, {true_label}")
                        case "<=": 
                            out_asm_text(f"ble $t6, $t7, {true_label}")
                        case "==": 
                            out_asm_text(f"beq $t6, $t7, {true_label}")
                        case "~=": 
                            out_asm_text(f"bne $t6, $t7, {true_label}")
                    
                    # False case - load 0
                    out_asm_text("li $t7, 0")
                    out_asm_text(f"j {end_label}")
                    
                    # True case - load 1
                    out_asm_text(f"{true_label}:")
                    out_asm_text("li $t7, 1")
                    
                    # End of comparison
                    out_asm_text(f"{end_label}:")
                    out_asm_text("pushw($t7)")
                    out_asm_text("# end of comparison node")

                case "if":
                    out_asm_text("# if statement")
                    
                    # create unique labels
                    false_label = f"false_{self.label_counter}"
                    end_label = f"end_{self.label_counter}"
                    self.label_counter += 1
                    
                    # Evaluate condition
                    emit(node.children[0])
                    out_asm_text("popw($t7)")
                    out_asm_text(f"beqz $t7, {false_label}")  # branching
                    
                    # true branch
                    emit(node.children[1])  # Execute 'then' part
                    out_asm_text(f"j {end_label}")
                    
                    # false branch
                    out_asm_text(f"{false_label}:")
                    if len(node.children) > 2:
                        emit(node.children[2])
                    
                    # End of if statement
                    out_asm_text(f"{end_label}:")
                    out_asm_text("# end of if statement")
                    
                case "while":
                    out_asm_text("# while loop")
                    
                    loop_start = f"while_start_{self.label_counter}"
                    loop_end = f"while_end_{self.label_counter}"
                    self.label_counter += 1
                    
                    # loop start
                    out_asm_text(f"{loop_start}:")
                    
                    # evaluation
                    emit(node.children[0])
                    out_asm_text("popw($t7)")  # Get condition result
                    out_asm_text(f"beqz $t7, {loop_end}")  # Exit loop if condition is false
                    
                    emit(node.children[1])  # Execute loop body
                    
                    # goto start
                    out_asm_text(f"j {loop_start}")
                    
                    # end
                    out_asm_text(f"{loop_end}:")
                    out_asm_text("# end of while loop")
                case _:
                    print(node.name)
                    # raise SyntaxWarning("Emitter error: AST node unknown: {}".format(node.name))

        # generate the assembly code
        emit(self.ast)

    def export_asm(self):
        f = open("asm_output.txt", "w")
        f.write(self.asm_data_section + "\n" + self.asm_text_section)
        f.close()