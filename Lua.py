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
    def run(self):
        while True:
            try:
                s = input('Lua > ')
            except EOFError:
                break
            if not s:
                continue
            yacc.parse(s)


class Calc(Parser):

    # noinspection SpellCheckingInspection
    tokens = (
        'NAME', 'NUMBER', 'FLOAT',
        'PLUS', 'MINUS', 'EXP', 'TIMES', 'DIVIDE', 'EQUALS',
        'LPAREN', 'RPAREN',
    )

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
    t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'

    # noinspection PyPep8Naming
    # noinspection PyMethodMayBeStatic
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
    
    def p_statement_assign(self, p):
        """statement : NAME EQUALS expression"""
        self.names[p[1]] = p[3]

    # noinspection PyMethodMayBeStatic
    def p_statement_expr(self, p):
        """statement : expression"""
        AST.render_tree(p[1])

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
        # print [repr(p[i]) for i in range(0,4)]
        if p[2] == '+':
            p[0] = AST("addition", children=[p[1], p[3]])
        elif p[2] == '-':
            p[0] = AST("subtraction", children=[p[1], p[3]])
        elif p[2] == '*':
            p[0] = AST("multiplication", children=[p[1], p[3]])
        elif p[2] == '/':
            p[0] = AST("division", children=[p[1], p[3]])
        elif p[2] == '**':
            p[0] = AST("exponentiation", children=[p[1], p[3]])

    # noinspection PyMethodMayBeStatic
    # noinspection SpellCheckingInspection
    def p_expression_uminus(self, p):
        """expression : MINUS expression %prec UMINUS"""
        p[0] = AST("number", value=-p[2])

    # noinspection SpellCheckingInspection
    # noinspection PyMethodMayBeStatic
    def p_expression_group(self, p):
        """expression : LPAREN expression RPAREN"""
        p[0] = AST("parentheses", children=[p[2]])

    # noinspection PyMethodMayBeStatic
    def p_expression_number(self, p):
        """expression : NUMBER"""
        p[0] = AST("number", value=p[1])

    def p_expression_float(self, p):
        """expression : FLOAT"""
        p[0] = AST("float", value=p[1])

    def p_expression_name(self, p):
        """expression : NAME"""
        try:
            p[0] = self.names[p[1]]
        except LookupError:
            print("Undefined name '%s'" % p[1])
            p[0] = 0

    # noinspection PyMethodMayBeStatic
    def p_error(self, p):
        if p:
            print("Syntax error at '%s'" % p.value)
        else:
            print("Syntax error at EOF")


if __name__ == '__main__':
    calc = Calc()
    calc.run()
