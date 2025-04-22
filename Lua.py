#!/usr/bin/env python

# -----------------------------------------------------------------------------
# calc.py
#
# A simple calculator with variables.   This is from O'Reilly's
# "Lex and Yacc", p. 63.
#
# Class-based example contributed to PLY by David McNab
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Updates by Deanna M. Wilborne
#   2024-04-29
#       * # noinspection PyMethodMayBeStatic added to methods that look static
#       * renamed debugfile to debug_file
#       * # noinspection SpellCheckingInspection added where needed
#       * # noqa added to __init__() for exception handling to supress warning
#       * # noinspection PyPep8Naming added where needed
#       * single quoted document strings converted to triple quoted
# -----------------------------------------------------------------------------


import ply.lex as lex
import ply.yacc as yacc
import os
from AST import AST

class Parser:
    """
    Base class for a lexer/parser that has the rules defined as methods
    """
    tokens = ()
    precedence = ()

    def __init__(self, **kw):
        self.debug = kw.get('debug', 0)
        self.names = {}
        try:
            modname = os.path.split(os.path.splitext(__file__)[0])[
                1] + "_" + self.__class__.__name__
        # 2024-04-29, DMW, TODO: figure out the appropriate exceptions to handle and narrow
        except:  # noqa
            modname = "parser" + "_" + self.__class__.__name__
        self.debug_file = modname + ".dbg"
        # print self.debug_file

        # Build the lexer and parser
        lex.lex(module=self, debug=self.debug)
        yacc.yacc(module=self,
                  debug=self.debug,
                  debugfile=self.debug_file)

    # noinspection PyMethodMayBeStatic
    def export_ast(self, source: str =None):
        s = """
a = 5
b = 3
c = a + b
d = 96
e = c + d
f = (e + -2) / 13
print(f)
        """
        stream = source if source else s
        inter_rep = yacc.parse(stream)
        AST.render_tree(inter_rep)
        return inter_rep



class Lua(Parser):
    def __init__(self, repl_prompt: str = "Ready >"):
        super().__init__(debug=1)  # add debug=1 to get .dbg file with grammar
        self.symbol_table = {}
        self.object_counter = 0
    
    def get_obj_ctr(self, label: str, type_info: str = "unknown") -> dict:
        if label in self.symbol_table:
            raise ValueError("Compile Error: value previously allocated in global vars: {}".format(label))
        address = "{}_{:05d}".format(label, self.object_counter)
        self.object_counter = self.object_counter + 1
        
        symbol_info = {
            "address": address,
            "type": type_info,
            "name": label
        }
    
        return symbol_info

    # noinspection SpellCheckingInspection
    tokens = [
        'ID', 'NUMBER', 'FLOAT', 'STRING',
        'PLUS', 'MINUS', 'EXP', 'TIMES', 'DIVIDE', 'EQUALS',
        'LPAREN', 'RPAREN'
    ]

    lua_keywords = {
        "and": "AND", "break": "BREAK", "do": "DO", "else": "ELSE", 
        "elseif": "ELSEIF", "end": "END", "false": "FALSE", "for": "FOR", 
        "function": "FUNCTION", "if": "IF", "in": "IN", "local": "LOCAL", 
        "nil": "NIL", "not": "NOT", "or": "OR", "print":"PRINT", "repeat": "REPEAT", 
        "return": "RETURN", "then": "THEN", "true": "TRUE", 
        "until": "UNTIL", "while": "WHILE", "id": "ID"
    }

    lua_keywords = {"print": "PRINT", "dot": "DOT"}

    tokens += [keyword for keyword in lua_keywords.values()]

    # Tokens

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_EXP = r'\*\*'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'
    t_EQUALS = r'='
    # noinspection SpellCheckingInspection
    t_LPAREN = r'\('
    # noinspection SpellCheckingInspection
    t_RPAREN = r'\)'
    t_DOT = r'\.'

    # noinspection PyPep8Naming
    # noinspection PyMethodMayBeStatic

    def t_STRING(self, t):
        r"""\"[^\"]*\"|\'[^\']*\'"""
        t.value = t.value[1:-1]
        return t
    
    def t_NUMBER(self, t):
        r"""(?<![\d.])[0-9]+(?![\d.])"""
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %s" % t.value)
            t.value = 0
        # print "parsed number %s" % repr(t.value)
        return t
    
    def t_FLOAT(self, t):
        r"""[-+]?[0-9]*(\.[0-9]+)"""
        try:
            t.value = float(t.value)
        except ValueError:
            print("Float value too large %s" % t.value)
            t.value = 0
        # print "parsed number %s" % repr(t.value)
        return t

    def t_ID(self, t):
        r"""[a-zA-Z_][a-zA-Z0-9_]*"""
    # if not keyword, then var ?
        id = str(t.value)
        t.type = self.lua_keywords.get(id, 'ID')
        if t.type == 'ID':
            if id in self.symbol_table:  # Note: Use id here, not t.value
                symbol_info = self.symbol_table[id]
                t.value = {'id': id, 'symbol': symbol_info["address"], 'type': symbol_info["type"]}
            else:
                # Create a new symbol and store it
                symbol_info = self.get_obj_ctr(id)
                self.symbol_table[id] = symbol_info
                t.value = {'id': id, 'symbol': symbol_info["address"], 'type': 'unknown'}
        return t
        

    t_ignore = " \t"

    # noinspection PyMethodMayBeStatic
    def t_newline(self, t):
        r"""\n+"""
        t.lexer.lineno += t.value.count("\n")

    # noinspection PyMethodMayBeStatic
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # Parsing rules

    # noinspection SpellCheckingInspection
    precedence = (
        ('left', 'PLUS', 'MINUS'),
        ('left', 'TIMES', 'DIVIDE'),
        ('left', 'EXP'),
        ('right', 'UMINUS'),
    )

    def p_program(self, p):
        """program : opt_stmts"""
        p[0] = AST("program", children=[p[1]])

    def p_opt_stmts(self, p):
        """opt_stmts : stmt_list"""
        p[0] = AST("opt_stmts", children=[p[1]])

    def p_opt_stmts2(self, p):
        """opt_stmts : """
        p[0] = AST("nop")

    def p_stmt_list(self, p):
        """stmt_list : statement"""
        p[0] = AST("stmt_list", children=[p[1]])

    def p_stmt_list2(self, p):
        """stmt_list : stmt_list statement"""
        p[1].children = list(p[1].children) + [p[2]]
        p[0] = p[1]

    def p_statement_assign(self, p):
        """statement : ID EQUALS expression"""
        # Frick man, this is growing complex. Tracking each assignment at parsing is crazy smart, it just might work
        expr_node = p[3]
        expr_type = "unknown"
        
        if expr_node.name == "string":
            expr_type = "string"
        elif expr_node.name == "number" or expr_node.name == "float":       # merging both for now
            expr_type = "number"
        
        # now update the symbol table
        var_name = p[1]['id']
        if var_name in self.symbol_table:
            self.symbol_table[var_name]["type"] = expr_type
        else:
            symbol_info = self.get_obj_ctr(var_name, expr_type)
            self.symbol_table[var_name] = symbol_info
        
        # add the type on the object ????
        p[1]['type'] = expr_type
        p[0] = AST("assignment", value=p[1], children=[p[3]])
        
    def p_statement_print(self, p):
        """statement : PRINT LPAREN expression RPAREN """
        p[0] = AST("print", value=p[1], children=[p[3]])

    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EXP expression
        """
        p[0] = AST("binop", value=p[2], children=[p[1], p[3]])
        p[0].type = "number"

    # noinspection PyMethodMayBeStatic
    # noinspection SpellCheckingInspection
    def p_expression_uminus(self, p):
        """expression : MINUS expression %prec UMINUS"""
        p[0] = AST("unary", value="UMINUS", children=[p[2]])

    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = AST("parentheses", children=[p[2]])

    # noinspection PyMethodMayBeStatic
    def p_expression_number(self, p):
        """expression : NUMBER"""
        p[0] = AST("number", value=p[1])
        p[0].type = "number"

    def p_expression_string(self, p):
        """expression : STRING"""
        p[0] = AST("string", value=p[1])
        p[0].type = "string"  # now adding types

    def p_expression_float(self, p):
        """expression : FLOAT"""
        p[0] = AST("float", value=p[1])

    def p_expression_ID(self, p):
        """expression : ID"""
        p[0] = AST("ID", value=p[1])

        if 'id' in p[1] and p[1]['id'] in self.symbol_table:
            p[0].type = self.symbol_table[p[1]['id']]["type"]
        elif 'type' in p[1]:
            p[0].type = p[1]['type']
        else:
            p[0].type = "unknown"

    def p_expression_io_read(self, p):
        """expression : ID DOT ID LPAREN STRING RPAREN
                    | ID DOT ID LPAREN RPAREN"""
        
        if p[1]['id'] == 'io' and p[3]['id'] == 'read':
            # Check if a format was provided
            if len(p) == 7:
                format_str = p[5]
                if format_str == "*n":
                    read_type = "number"
                elif format_str == "*l" or format_str == "*a":
                    read_type = "string"
                else:
                    read_type = "string"
            else: 
                read_type = "string"  # Default behavior is to read a line
            
            p[0] = AST("io_read", value=read_type)
            p[0].type = read_type
        else:
            raise Exception("I'm not handling this yet man")

    # noinspection PyMethodMayBeStatic
    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")


if __name__ == '__main__':
    lua = Lua()
    lua.export_ast()
