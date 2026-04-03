import ply.yacc as yacc
from lexer import tokens
from models import (
    SelectNode, InsertNode, CreateTableNode, DropTableNode,
    IdentifierNode, LiteralNode, BinaryOpNode, JoinNode, AggregateNode
)

# --- 1. Operator Precedence ---
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUALS', 'NEQ', 'GE', 'LE', 'GT', 'LT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'STAR'),
)

# --- 2. Top-Level Statements ---
def p_statement(p):
    '''statement : select_stmt
                 | insert_stmt
                 | create_stmt
                 | drop_stmt'''
    p[0] = p[1]

# --- 3. SELECT Logic ---
def p_select_stmt(p):
    '''select_stmt : SELECT projections FROM IDENTIFIER opt_joins opt_where opt_groupby opt_semicolon'''
    p[0] = SelectNode(
        projections=p[2],
        from_table=p[4],
        joins=p[5],
        where=p[6],
        group_by=p[7]
    )

def p_projections_all(p):
    'projections : STAR'
    p[0] = ["*"]

def p_projections_list(p):
    '''projections : projection_item
                   | projections COMMA projection_item'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

# --- Updated to handle Qualified Projections (Table.Column) ---
def p_projection_item(p):
    '''projection_item : qualified_id
                       | aggregate_func'''
    p[0] = p[1]

def p_aggregate_func(p):
    '''aggregate_func : SUM LPAREN qualified_id RPAREN
                      | COUNT LPAREN qualified_id RPAREN
                      | AVG LPAREN qualified_id RPAREN
                      | MIN LPAREN qualified_id RPAREN
                      | MAX LPAREN qualified_id RPAREN'''
    p[0] = AggregateNode(func=p[1], column=p[3])

# --- 4. JOIN Logic ---
def p_opt_joins(p):
    '''opt_joins : join_list
                 | empty'''
    p[0] = p[1] if p[1] else []

def p_join_list(p):
    '''join_list : join_item
                 | join_list join_item'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_join_item(p):
    '''join_item : join_type JOIN IDENTIFIER ON expression'''
    p[0] = JoinNode(join_type=p[1], table=p[3], on_condition=p[5])

def p_join_type(p):
    '''join_type : INNER
                 | LEFT
                 | RIGHT
                 | FULL
                 | CROSS
                 | empty'''
    p[0] = p[1] if p[1] else "INNER"

# --- 5. Expressions (WHERE & Math) ---
def p_opt_where(p):
    '''opt_where : WHERE expression
                 | empty'''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = None

def p_expression_binop(p):
    '''expression : expression EQUALS expression
                  | expression NEQ expression
                  | expression GT expression
                  | expression LT expression
                  | expression GE expression
                  | expression LE expression
                  | expression AND expression
                  | expression OR expression
                  | expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    p[0] = BinaryOpNode(left=p[1], op=p[2], right=p[3])

# --- Updated to handle Qualified Identifiers in Expressions ---
def p_expression_term(p):
    '''expression : qualified_id
                  | NUMBER
                  | STRING
                  | TRUE
                  | FALSE'''
    # This logic matches your LiteralNode implementation
    if p.slice[1].type == 'NUMBER':
        p[0] = LiteralNode(p[1], 'NUMBER')
    elif p.slice[1].type == 'STRING':
        p[0] = LiteralNode(p[1], 'STRING')
    elif p.slice[1].type == 'TRUE':
        p[0] = LiteralNode(True, 'BOOLEAN')
    elif p.slice[1].type == 'FALSE':
        p[0] = LiteralNode(False, 'BOOLEAN')
    else:
        p[0] = p[1]

# --- NEW: Rule for Table.Column syntax ---
def p_qualified_id(p):
    '''qualified_id : IDENTIFIER DOT IDENTIFIER
                    | IDENTIFIER'''
    if len(p) > 2:
        p[0] = IdentifierNode(name=p[3], table=p[1])
    else:
        p[0] = IdentifierNode(name=p[1])

# --- 6. DDL & DML ---
def p_create_stmt(p):
    'create_stmt : CREATE TABLE IDENTIFIER LPAREN column_defs RPAREN'
    p[0] = CreateTableNode(table_name=p[3], columns=p[5])

def p_column_defs(p):
    '''column_defs : column_def
                   | column_defs COMMA column_def'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_column_def(p):
    '''column_def : IDENTIFIER data_type'''
    p[0] = {'name': p[1], 'type': p[2]}

def p_data_type(p):
    '''data_type : INT
                 | TEXT
                 | FLOAT'''
    p[0] = p[1]

def p_insert_stmt(p):
    'insert_stmt : INSERT INTO IDENTIFIER VALUES LPAREN value_list RPAREN'
    p[0] = InsertNode(table=p[3], values=p[6])

def p_value_list(p):
    '''value_list : expression
                  | value_list COMMA expression'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_drop_stmt(p):
    'drop_stmt : DROP TABLE IDENTIFIER'
    p[0] = DropTableNode(table_name=p[3])

# --- 7. Boilerplate & Error ---
def p_opt_groupby(p):
    '''opt_groupby : GROUP BY qualified_id
                   | empty'''
    if len(p) > 2:
        p[0] = [p[3]]
    else:
        p[0] = None

def p_opt_semicolon(p):
    '''opt_semicolon : SEMICOLON
                     | empty'''
    pass

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p:
        raise SyntaxError(f"Syntax Error: Unexpected '{p.value}' at token {p.type}")
    else:
        raise SyntaxError("Syntax Error: Unexpected end of input")

parser = yacc.yacc()

def parse_sql(data):
    return parser.parse(data)