import ply.lex as lex

# 1. List of token names
# FIX: Added 'TRUE' and 'FALSE' to this tuple so the Parser can recognize them
tokens = (
    'NUMBER', 'STRING', 'IDENTIFIER',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE',
    'EQUALS', 'NEQ', 'GE', 'LE', 'GT', 'LT',
    'COMMA', 'LPAREN', 'RPAREN', 'SEMICOLON', 'DOT', 'STAR',
    'SELECT', 'FROM', 'WHERE', 'JOIN', 'ON', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS',
    'AND', 'OR', 'IN', 'BETWEEN', 'GROUP', 'BY', 'HAVING', 'INSERT', 'INTO', 'VALUES',
    'UPDATE', 'SET', 'DELETE', 'CREATE', 'TABLE', 'DROP', 'ALTER', 'ADD',
    'INT', 'TEXT', 'FLOAT', 'SUM', 'COUNT', 'AVG', 'MIN', 'MAX',
    'TRUE', 'FALSE' 
)

# 2. Reserved words dictionary
reserved = {
    'select': 'SELECT', 'from': 'FROM', 'where': 'WHERE', 'join': 'JOIN',
    'on': 'ON', 'inner': 'INNER', 'left': 'LEFT', 'right': 'RIGHT',
    'full': 'FULL', 'cross': 'CROSS', 'and': 'AND', 'or': 'OR',
    'in': 'IN', 'between': 'BETWEEN', 'group': 'GROUP', 'by': 'BY',
    'having': 'HAVING', 'insert': 'INSERT', 'into': 'INTO', 'values': 'VALUES',
    'update': 'UPDATE', 'set': 'SET', 'delete': 'DELETE', 
    'create': 'CREATE', 'table': 'TABLE', 'drop': 'DROP', 
    'alter': 'ALTER', 'add': 'ADD',
    'int': 'INT', 'text': 'TEXT', 'float': 'FLOAT',
    'sum': 'SUM', 'count': 'COUNT', 'avg': 'AVG', 'min': 'MIN', 'max': 'MAX',
    'true': 'TRUE',
    'false': 'FALSE'
}

# 3. Simple regex rules for operators and delimiters
t_PLUS      = r'\+'
t_MINUS     = r'-'
t_TIMES     = r'\*'
t_STAR      = r'\*' 
t_DIVIDE    = r'/'
t_EQUALS    = r'='
t_NEQ       = r'!='
t_GE        = r'>='
t_LE        = r'<='
t_GT        = r'>'
t_LT        = r'<'
t_COMMA     = r','
t_LPAREN    = r'\('
t_RPAREN    = r'\)'
t_SEMICOLON = r';'
t_DOT       = r'\.'

# 4. Complex Regex rules
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_STRING(t):
    r"'(?:''|[^'])*'"
    t.value = t.value[1:-1].replace("''", "'") 
    return t

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Standardizing to UPPER for the Parser's reserved word check
    t.type = reserved.get(t.value.lower(), 'IDENTIFIER')
    return t

def t_QUOTED_IDENTIFIER(t):
    r'\"[a-zA-Z_][a-zA-Z0-9_]*\"'
    t.value = t.value[1:-1]
    t.type = 'IDENTIFIER'
    return t

# Ignored characters
t_ignore = ' \t\n'

# Error handling
def t_error(t):
    error_msg = f"Lexical Error: Illegal character '{t.value[0]}' at position {t.lexpos}"
    t.lexer.skip(1)
    raise SyntaxError(error_msg)

# Build the lexer
lexer = lex.lex()