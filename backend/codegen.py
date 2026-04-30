# backend/codegen.py
import psycopg2
from psycopg2.extras import RealDictCursor

class CodeGenerator:
    def __init__(self):
        self.code_lines = []
        self.indent = "    "

    def generate(self, optimized_plan):
        """Entry point for code generation. This is what main.py calls."""
        self.code_lines = [
            "import psycopg2",
            "from psycopg2.extras import RealDictCursor",
            "",
            "def execute_compiled_query(conn_string):",
            f"{self.indent}conn = psycopg2.connect(conn_string)",
            f"{self.indent}cur = conn.cursor(cursor_factory=RealDictCursor)",
            f"{self.indent}result_data = []",
            "",
            f"{self.indent}# Helper to handle case-sensitive keys from the database",
            f"{self.indent}def get_val(r, k):",
            f"{self.indent}{self.indent}actual_key = next((key for key in r.keys() if key.lower() == k.lower()), k)",
            f"{self.indent}{self.indent}return r.get(actual_key)",
            ""
        ]
        
        # Start the recursive translation of the plan
        self._translate_op(optimized_plan)
        
        self.code_lines.extend([
            f"{self.indent}cur.close()",
            f"{self.indent}conn.close()",
            f"{self.indent}return result_data"
        ])
        
        return "\n".join(self.code_lines)

    def _build_python_expr(self, node):
        """Recursively converts AST nodes into Null-safe Python strings for SELECT & HAVING filters."""
        if not node: return "True"
        
        node_type = node.__class__.__name__
        
        if node_type == "LiteralNode":
            if getattr(node, 'data_type', '') == 'STRING' or isinstance(node.value, str): 
                return f"'{node.value}'"
            return str(node.value)
            
        elif node_type == "IdentifierNode":
            name = node.name if hasattr(node, 'name') else str(node)
            return f"get_val(row, '{name}')"
            
        elif node_type == "AggregateNode":
            # The AGGREGATE step saved the result under the lowercase function name (e.g., 'count')
            return f"get_val(row, '{node.func.lower()}')"
            
        elif node_type == "BinaryOpNode":
            # Recursively build left and right sides for math and logic
            left = self._build_python_expr(node.left)
            right = self._build_python_expr(node.right)
            
            op_map = {
                'EQUALS': '==', '=': '==', 'NEQ': '!=', '!=': '!=',
                'GT': '>', '>': '>', 'LT': '<', '<': '<', 
                'GE': '>=', '>=': '>=', 'LE': '<=', '<=': '<=', 
                'AND': 'and', 'OR': 'or', 'PLUS': '+', '+': '+',
                'MINUS': '-', '-': '-', 'STAR': '*', '*': '*',
                'DIVIDE': '/', '/': '/'
            }
            py_op = op_map.get(node.op.upper() if hasattr(node.op, 'upper') else node.op, '==')
            
            if py_op == '/':
                # Safety: Return 0 if the denominator is 0 instead of crashing
                return f"({left} / {right} if {right} != 0 else 0)"
            
            # --- THE FIX: Smart Null-Checking ---
            if py_op in ['<', '>', '<=', '>=']:
                # Only check for None if the value is actually a database column (contains 'get_val')
                left_safe = f"{left} is not None" if "get_val" in left else "True"
                right_safe = f"{right} is not None" if "get_val" in right else "True"
                
                return f"({left_safe} and {right_safe} and float({left}) {py_op} float({right}))"
            
            return f"({left} {py_op} {right})"
                    
        # Fallbacks
        if hasattr(node, 'name'):
           return f"get_val(row, '{node.name}')"
        if hasattr(node, 'value'):
            return repr(node.value)
            
        return "True"

    def _build_sql_where(self, node):
        """Helper to translate AST conditions back to SQL strings for DELETE/UPDATE."""
        if not node: return ""
        if hasattr(node, 'name'):
            return f'"{node.name}"'
        if hasattr(node, 'value'):
            return repr(node.value)
        if hasattr(node, 'left') and hasattr(node, 'right'):
            return f"({self._build_sql_where(node.left)} {node.op} {self._build_sql_where(node.right)})"
        return ""

    def _translate_op(self, op):
        if not op:
            return

        if hasattr(op, 'source') and op.source:
            self._translate_op(op.source)
            
        db_ops = ["SCAN", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "METADATA", "JOIN"]
        current_indent = (self.indent + self.indent) if op.op_type in db_ops else self.indent
        
        if op.op_type in db_ops:
            self.code_lines.append(f"{self.indent}try:")
            
        if op.op_type == "SCAN":
            table = op.params['table']
            self.code_lines.append(f"{current_indent}# Phase: SCAN \"{table}\"")
            self.code_lines.append(f"{current_indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{current_indent}result_data = cur.fetchall()")

        elif op.op_type == "FILTER":
            cond = op.params['condition']
            py_expression = self._build_python_expr(cond)
            self.code_lines.append(f"{current_indent}# Phase: FILTER")
            self.code_lines.append(f"{current_indent}result_data = [row for row in result_data if {py_expression}]")

        elif op.op_type == "PROJECT":
            cols = op.params.get('columns', [])
            self.code_lines.append(f"{self.indent}# Phase: PROJECT (with Math & Aliases)")
            
            if cols and cols != ["*"]:
                self.code_lines.append(f"{self.indent}projected_data = []")
                self.code_lines.append(f"{self.indent}for row in result_data:")
                self.code_lines.append(f"{self.indent}{self.indent}new_row = {{}}")
                
                for col in cols:
                    if col.__class__.__name__ == "AliasNode":
                        # Evaluate the complex math/logic inside the alias
                        expr_str = self._build_python_expr(col.expr)
                        self.code_lines.append(f"{self.indent}{self.indent}new_row['{col.alias}'] = {expr_str}")
                    else:
                        # Standard column without an AS clause
                        expr_str = self._build_python_expr(col)
                        col_name = col.name if hasattr(col, 'name') else "col"
                        self.code_lines.append(f"{self.indent}{self.indent}new_row['{col_name}'] = {expr_str}")
                        
                self.code_lines.append(f"{self.indent}{self.indent}projected_data.append(new_row)")
                self.code_lines.append(f"{self.indent}result_data = projected_data")
                                                            
        elif op.op_type == "JOIN":
            table, on_cond = op.params['table'], op.params['on']
            self.code_lines.append(f"{current_indent}# Phase: JOIN \"{table}\"")
            self.code_lines.append(f"{current_indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{current_indent}join_table_data = cur.fetchall()")
            self.code_lines.append(f"{current_indent}joined_results = []")
            
            if on_cond:
                # Standard Join logic
                l_key, r_key = on_cond.left.name, on_cond.right.name
                self.code_lines.append(f"{current_indent}for r1 in result_data:")
                self.code_lines.append(f"{current_indent}{self.indent}for r2 in join_table_data:")
                self.code_lines.append(f"{current_indent}{self.indent}{self.indent}if get_val(r1, '{l_key}') == get_val(r2, '{r_key}'):")
                self.code_lines.append(f"{current_indent}{self.indent}{self.indent}{self.indent}joined_results.append({{**r1, **r2}})")
            else:
                # CROSS JOIN logic: Pair every row with every other row
                self.code_lines.append(f"{current_indent}for r1 in result_data:")
                self.code_lines.append(f"{current_indent}{self.indent}for r2 in join_table_data:")
                self.code_lines.append(f"{current_indent}{self.indent}{self.indent}joined_results.append({{**r1, **r2}})")
            
            self.code_lines.append(f"{current_indent}result_data = joined_results")
            
        elif op.op_type == "INSERT":
            table = op.params['table']
            values_list = op.params['values'] 
            
            # Unpack the AST nodes into a raw SQL VALUES string
            tuple_strings = []
            for row in values_list:
                row_vals = []
                for node in row:
                    if hasattr(node, 'value'):
                        if node.value is None:
                            row_vals.append("NULL")
                        elif isinstance(node.value, str):
                            row_vals.append(f"'{node.value}'")
                        else:
                            row_vals.append(str(node.value))
                    elif hasattr(node, 'name'): 
                        # Fallback just in case something parses as an identifier
                        row_vals.append("NULL" if node.name.upper() == "NULL" else f"'{node.name}'")
                    else:
                        row_vals.append(str(node))
                
                tuple_strings.append(f"({', '.join(row_vals)})")
                
            all_values_str = ", ".join(tuple_strings)
            
            self.code_lines.append(f"{current_indent}# Phase: Multi-row INSERT")
            self.code_lines.append(f"{current_indent}sql = f'''INSERT INTO \"{table}\" VALUES {all_values_str}'''")
            self.code_lines.append(f"{current_indent}cur.execute(sql)")
            self.code_lines.append(f"{current_indent}conn.commit()")
            # THE FIX: Removed the inner 'f' and single curly braces for len(values_list)
            self.code_lines.append(f"{current_indent}result_data = [{{'status': 'success', 'message': 'Inserted {len(values_list)} row(s)'}}]")
                
        elif op.op_type == "DELETE":
            table, cond = op.params['table'], op.params['condition']
            where_sql = f" WHERE {self._build_sql_where(cond)}" if cond else ""
            self.code_lines.append(f"{current_indent}sql = f'''DELETE FROM \"{table}\"{where_sql}'''")
            self.code_lines.append(f"{current_indent}cur.execute(sql)")
            self.code_lines.append(f"{current_indent}conn.commit()")
            self.code_lines.append(f"{current_indent}result_data = [{{'status': 'success', 'rows': cur.rowcount}}]")

        elif op.op_type == "UPDATE":
            table, assigns, cond = op.params['table'], op.params['assigns'], op.params['condition']
            formatted_assigns = []
            for a in assigns:
                val = a["value"].value if hasattr(a["value"], "value") else a["value"]
                formatted_assigns.append(f'"{a["column"]}" = {repr(val)}')
            set_clause = ", ".join(formatted_assigns)
            where_sql = f" WHERE {self._build_sql_where(cond)}" if cond else ""
            self.code_lines.append(f"{current_indent}sql = f'''UPDATE \"{table}\" SET {set_clause}{where_sql}'''")
            self.code_lines.append(f"{current_indent}cur.execute(sql)")
            self.code_lines.append(f"{current_indent}conn.commit()")
            self.code_lines.append(f"{current_indent}result_data = [{{'status': 'success', 'rows': cur.rowcount}}]")
            
        elif op.op_type == "CREATE":
            table, cols = op.params['table'], op.params['columns']
            col_defs = ", ".join([f'"{c["name"]}" {c["type"]}' for c in cols])
            self.code_lines.append(f"{current_indent}cur.execute('CREATE TABLE \"{table}\" ({col_defs})')")
            self.code_lines.append(f"{current_indent}conn.commit()")
            self.code_lines.append(f"{current_indent}result_data = [{{'status': 'success', 'table': '{table}'}}]")

        elif op.op_type == "DROP":
            table = op.params['table']
            self.code_lines.append(f"{current_indent}cur.execute('DROP TABLE IF EXISTS \"{table}\"')")
            self.code_lines.append(f"{current_indent}conn.commit()") # <--- ADD THIS EXACT LINE
            self.code_lines.append(f"{current_indent}result_data = [{{'status': 'success', 'message': 'Dropped {table}'}}]")
                        
        elif op.op_type == "METADATA":
            self.code_lines.append(f"{current_indent}cur.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\")")
            self.code_lines.append(f"{current_indent}result_data = cur.fetchall()")

        if op.op_type in db_ops:
            self.code_lines.append(f"{self.indent}except psycopg2.Error as e:")
            self.code_lines.append(f"{self.indent}{self.indent}return [{{'status': 'error', 'message': f'Database Error: {{e.pgerror or str(e)}}'}}]")

        elif op.op_type == "SORT":
            col, ascending = op.params['column'], op.params['ascending']
            # We use 'or ""' and 'or 0' to ensure we don't compare NoneTypes during sorting
            self.code_lines.append(f"{self.indent}result_data.sort(key=lambda x: (get_val(x, '{col}') or ''), reverse={not ascending})")
                        
        # --- ADD THIS BLOCK ---
        elif op.op_type == "LIMIT":
            limit_val = op.params['value']
            self.code_lines.append(f"{self.indent}# Phase: LIMIT")
            self.code_lines.append(f"{self.indent}result_data = result_data[:{limit_val}]")
            
        elif op.op_type == "AGGREGATE":
            group_cols = op.params.get('columns', [])
            funcs = op.params.get('functions', [])
            having_cond = op.params.get('having')
            
            if group_cols:
                self.code_lines.append(f"{self.indent}buckets = {{}}")
                self.code_lines.append(f"{self.indent}for row in result_data:")
                
                # Create a tuple key: (val1, val2, ...)
                col_names = [c.name if hasattr(c, 'name') else c for c in group_cols]
                key_str = ", ".join([f"get_val(row, '{name}')" for name in col_names])
                
                # THE FIX: Added a trailing comma here -> ({key_str},)
                # This guarantees it evaluates as a tuple even with a single NULL value
                self.code_lines.append(f"{self.indent}{self.indent}key = ({key_str},)")
                
                self.code_lines.append(f"{self.indent}{self.indent}if key not in buckets: buckets[key] = []")
                self.code_lines.append(f"{self.indent}{self.indent}buckets[key].append(row)")
                
                self.code_lines.append(f"{self.indent}result_data = []")
                self.code_lines.append(f"{self.indent}for key, rows in buckets.items():")
                
                # Unpack the tuple key back into the result dict
                self.code_lines.append(f"{self.indent}{self.indent}res = {{}}")
                for i, name in enumerate(col_names):
                    self.code_lines.append(f"{self.indent}{self.indent}res['{name}'] = key[{i}]")

                for f in funcs:
                    f_name = f.func.lower()
                    c_name = f.column.name if hasattr(f.column, 'name') else f.column
                    if f.func == 'COUNT':
                        self.code_lines.append(f"{self.indent}{self.indent}res['{f_name}'] = len(rows)")
                    elif f.func == 'SUM':
                        self.code_lines.append(f"{self.indent}{self.indent}res['{f_name}'] = sum(float(get_val(r, '{c_name}')) for r in rows if get_val(r, '{c_name}') is not None)")
                    elif f.func == 'AVG':
                        self.code_lines.append(f"{self.indent}{self.indent}res['{f_name}'] = sum(float(get_val(r, '{c_name}')) for r in rows if get_val(r, '{c_name}') is not None) / len(rows) if rows else 0")
                
                self.code_lines.append(f"{self.indent}{self.indent}result_data.append(res)")
            else:
                self.code_lines.append(f"{self.indent}res = {{}}")
                for f in funcs:
                    f_name = f.func.lower()
                    c_name = f.column.name if hasattr(f.column, 'name') else f.column
                    if f.func == 'COUNT':
                        self.code_lines.append(f"{self.indent}res['{f_name}'] = len(result_data)")
                    elif f.func == 'SUM':
                        self.code_lines.append(f"{self.indent}res['{f_name}'] = sum(float(get_val(r, '{c_name}')) for r in result_data if get_val(r, '{c_name}') is not None)")
                self.code_lines.append(f"{self.indent}result_data = [res]")
                
            # --- THE HAVING Filter Phase ---
            if having_cond:
                self.code_lines.append(f"{self.indent}# Phase: HAVING (Post-Aggregation Filter)")
                py_having = self._build_python_expr(having_cond)
                self.code_lines.append(f"{self.indent}result_data = [row for row in result_data if {py_having}]")
                                                                
        elif op.op_type == "SET_OP":
            self._translate_op(op.params['left'])
            self.code_lines.append(f"{self.indent}left_side = result_data")
            self._translate_op(op.params['right'])
            self.code_lines.append(f"{self.indent}right_side = result_data")
            if op.params['op'] == "UNION":
                self.code_lines.append(f"{self.indent}result_data = [dict(t) for t in {{tuple(d.items()) for d in left_side + right_side}}]")
        
        elif op.op_type == "SUBQUERY_SCAN":
            self.code_lines.append(f"{self.indent}# Phase: SUBQUERY SCAN (Virtual Table Ready)")