"""
 Author:
Created:
Purpose:
 Course:

  Notes:

History:

minicomp Base Compiler Revision History
2024-03-31, modified grammar to handle multiple lines, since most useful programs have more than one line
2024-02-27, created

"""

# ------------------------------------------------ STEP 1: PRELIMINARIES  / ENVIRONMENT SETUP
# import the libraries we'll need
import ply.lex as lex               # lexical analysis / tokenization
import ply.yacc as yacc             # parser
from AST import AST         # simple class for creating nodes for an Abstract Syntax Tree (AST)
from Common import Common           # a useful class and method for getting the type of an object
from ReadFile import ReadFile       # a simple but a useful read file class


# ------------------------------------------------ STEP 2: SET UP LEXER

"""
    See Section 4 of https://www.dabeaz.com/ply/ply.html. Sections 4 through 4.4.

    To handle reserved words, you should write a single rule to match an identifier and do a special name lookup
    in a function like this:

    reserved = {
       'if' : 'IF',
       'then' : 'THEN',
       'else' : 'ELSE',
       'while' : 'WHILE',
       ...
    }
    
    Note:
            * t_ definitions with regular expressions do not need to be created for reserved words
            * reserved words represent concrete syntax in the source language of your compiler
"""
reserved = {}

"""
    Tokens are elements of your grammar that are not reserved words, for example an ID for an identifier,
    or DQ_STRING for a string wrapped with double quotes. A list of tokens is required.
    
    Example: tokens = ['ID', 'NUMBER', ... ]
"""
# noinspection SpellCheckingInspection
tokens = [
    'NUMBER'
]

tokens += list(reserved.values())

"""
    See Section 4.8 of https://www.dabeaz.com/ply/ply.html.
    
    Literals are single characters that you will use in your language's concrete syntax but do not need
    t_ definitions created for them.
    
    Example: literals = ['(', ')', "+", "-", "%", "*", "/", "=", ";"]
"""
literals = []

# ------------------------------------------------ STEP 2.B.: SET UP LEXER T_RULES
# put all def t_ ... () definitions in this section
# NOTES:
# 1. Don't forget to add "return t" to each of your definitions
# 2. Use """ (document string) for literals that don't require a regular expression (most tokens don't require
#    regular expressions
# 3. Longer tokens should come before shorter tokens, or in other words """while""" is longer than
#    """<=""""; the definition for while should come before the definition for <=


# ------------------------------------------------ STEP 2.B.: END LEXER T_RULES

# helper function create a Python int or float as needed
# 2024-04-27, DMW, converted return value to dictionary
def string_to_number(s):
    try:
        ans = {'value': int(s), 'type': 'int'}
    except ValueError:
        ans = {'value': float(s), 'type': 'float'}

    return ans


# 2024-04-27, DMW, added source line number and character position within source relative to
#                  the beginning of the source to dictionary for the number token
# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
def t_NUMBER(t):
    r'[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?'  # 2024-02-14, DMW, we'll save floating point for later
    # https://www.regular-expressions.info/floatingpoint.html
    # r'\d+'  # original regular expression -- allow integers only

    token_value = string_to_number(t.value) # int(t.value)
    token_value['line_no'] = t.lexer.lineno
    token_value['src_pos'] = t.lexpos
    t.value = token_value # int(t.value)

    return t


# See section 4.5 - https://www.dabeaz.com/ply/ply.html - Lexer rules for ignoring text for tokenization
# noinspection PyPep8Naming
def t_COMMENT(t):
    r'\#.*'
    pass
    # No return value. Token discarded


# See sections 4.6, 4.7 - https://www.dabeaz.com/ply/ply.html
# characters to ignore as whitespace, space, tab, vertical tab, form feed
t_ignore = " \t\v\f"


# noinspection PySingleQuotedDocstring
def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")


# Compute column.
#     input is the input text string
#     token is a token instance
def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1


# See sections 4.9 - Error Handling - https://www.dabeaz.com/ply/ply.html
def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


# See sections 4.10 - EOF Handling- https://www.dabeaz.com/ply/ply.html
# Note: This method is not required and may not be necessary
# EOF handling rule
# def t_eof(t):
#     # Get more input (Example)
#     more = raw_input('... ')
#     if more:
#         self.lexer.input(more)
#         return self.lexer.token()
#     return None


# See sections 4.11 - Building and using the lexer - https://www.dabeaz.com/ply/ply.html
# Build the lexer
lexer = lex.lex()  # use parameter debug=1 for lexer debugging, see PLY manual

# ------------------------------------------------ STEP 3: SET UP THE PARSER

# Note: example precedence shown, setting precedence helps with binary operators
# noinspection SpellCheckingInspection
# precedence = (
#     ('left', 'LT', 'LE', 'EQ', 'NEQ', 'GE', 'GT'),
#     ('left', '+', '-'),
#     ('left', '*', '/', '%'),
#     ('right', 'UMINUS'),
# )

program = None

start = "program"  # set the start production, even though the first production is the start by default


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
# noinspection SpellCheckingInspection
def p_PROGRAM(p):
    "program : opt_stmts"
    global program
    program = AST("program", children=[p[1]])


# 2024-03-31, added to make it possible to have an empty program
# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
# noinspection SpellCheckingInspection
def p_optional_stmts(p):
    """opt_stmts : statement_list
                 | null"""
    p[0] = AST("opt_stmts", children=[p[1]])


# 2024-03-31, permit the null program to generate a tree with a NOP (no operation)
# this can also be used for optional parameter lists
# noinspection PyPep8Naming
def p_NULL(p):
    """null : """
    p[0] = AST("nop")
    return p


# noinspection PyPep8Naming
# noinspection PySingleQuotedDocstring
# noinspection SpellCheckingInspection
def p_statement_list(p):
    "statement_list : statement_list statement"
    p[0] = AST("statement_list", children=[p[1], p[2]])


# noinspection PyPep8Naming
def p_statement_list2(p):
    "statement_list : statement"
    p[0] = AST("statement_list", children=[p[1]])


# noinspection PyPep8Naming
def p_statement(p):
    "statement : number"
    p[0] = AST("number", children=[p[1]])


# noinspection PyPep8Naming
# def p_nop(p):
#     "nop : "  # what follows is null or <EMPTY>
#     p[0] = AST("nop")


# noinspection PyPep8Naming
def p_NUMBER(p):
    "number : NUMBER"
    p[0] = AST("number", value=p[1])
    # print(p[1])  # debugging


# a p_error(p) rule is required
# 2024-04-29, DMW, this useful definition is from:
# https://stackoverflow.com/questions/26979715/debugging-ply-in-p-error-to-access-parser-state-stack
def p_error(p):

    # get formatted representation of stack
    stack_state_str = ' '.join([symbol.type for symbol in parser.symstack][1:])

    print('Syntax error in input! Parser State:{} {} . {}'
          .format(parser.state,
                  stack_state_str,
                  p))


parser = yacc.yacc()  # use parameter debug=1 for parser debugging, see PLY manual for details

# ------------------------------------------------ STEP 4: USE THE PARSER

if __name__ == "__main__":
    # 2024-04-27, DMW, added this useful function for showing the token stream
    # call with source before parsing to see a list of tokens which can be useful for debugging the lexer
    # where problems in lexing often result in hard to understand parser errors
    def show_tokenization(source: str) -> None:
        # Give the lexer some input
        lexer.input(source)

        # Tokenize
        while True:
            tok = lexer.token()
            if not tok:
                break  # No more input
            print(tok)

    source_program = "17 18 19"

    # optional: show tokens and stop
    show_tokenization(source_program)
    # quit()

    ast = parser.parse(source_program)

    print(program)
    AST.render_tree(program)
