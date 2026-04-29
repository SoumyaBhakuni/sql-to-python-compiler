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
        """Recursively converts AST nodes into Null-safe Python strings for SELECT filters."""
        if hasattr(node, 'name'):
           return f"get_val(row, '{node.name}')"
    
        if hasattr(node, 'value'):
            return repr(node.value)

        if hasattr(node, 'left') and hasattr(node, 'right'):
            left_part = self._build_python_expr(node.left)
            right_part = self._build_python_expr(node.right)
        
            op_map = {'=': '==', 'AND': 'and', 'OR': 'or', 'NEQ': '!='}
            py_op = op_map.get(node.op.upper(), node.op)
        
            if py_op in ['<', '>', '<=', '>=', '==', '!=']:
               return f"({left_part} is not None and {left_part} {py_op} {right_part})"
        
            return f"({left_part} {py_op} {right_part})"
    
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
            cols = op.params['columns']
            self.code_lines.append(f"{self.indent}# Phase: PROJECT")
            has_aggregates = any(hasattr(c, 'func') for c in cols)
            if has_aggregates:
                self.code_lines.append(f"{self.indent}pass")
            else:
                col_names = [c.name if hasattr(c, 'name') else str(c) for c in cols]
                if "*" in col_names:
                    self.code_lines.append(f"{self.indent}# Keep all (SELECT *)")
                else:
                    col_list = ", ".join([f"'{c}'" for c in col_names])
                    self.code_lines.append(f"{self.indent}result_data = [{{c: get_val(row, c) for c in [{col_list}]}} for row in result_data]")
                    
        elif op.op_type == "JOIN":
            table, on_cond = op.params['table'], op.params['on']
            self.code_lines.append(f"{current_indent}# Phase: JOIN \"{table}\"")
            self.code_lines.append(f"{current_indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{current_indent}join_table_data = cur.fetchall()")
            self.code_lines.append(f"{current_indent}joined_results = []")
            l_key, r_key = on_cond.left.name, on_cond.right.name
            self.code_lines.append(f"{current_indent}for r1 in result_data:")
            self.code_lines.append(f"{current_indent}{self.indent}for r2 in join_table_data:")
            self.code_lines.append(f"{current_indent}{self.indent}{self.indent}if get_val(r1, '{l_key}') == get_val(r2, '{r_key}'):")
            self.code_lines.append(f"{current_indent}{self.indent}{self.indent}{self.indent}joined_results.append({{**r1, **r2}})")
            self.code_lines.append(f"{current_indent}result_data = joined_results")

        elif op.op_type == "INSERT":
            table = op.params['table']
            vals = op.params['values']
            
            # Helper to extract raw values from IdentifierNodes or ValueNodes
            def get_raw(v):
                if hasattr(v, 'name'): return v.name
                if hasattr(v, 'value'): return v.value
                return v

            if not vals:
                self.code_lines.append(f"{current_indent}result_data = [{{'status': 'error', 'message': 'No values'}}]")
            else:
                self.code_lines.append(f"{current_indent}# Phase: INSERT with PK Validation")
                pk_val = get_raw(vals[0])
                self.code_lines.append(f"{current_indent}pk_val = {repr(pk_val)}")
                self.code_lines.append(f"{current_indent}cur.execute(f'SELECT 1 FROM \"{table}\" WHERE \"studentId\" = %s', (pk_val,))")
                self.code_lines.append(f"{current_indent}if cur.fetchone():")
                self.code_lines.append(f"{current_indent}{self.indent}result_data = [{{'status': 'error', 'message': f'Primary Key {{pk_val}} already exists.'}}]")
                self.code_lines.append(f"{current_indent}else:")
                
                raw_vals = [get_raw(v) for v in vals]
                val_str = ", ".join([repr(v) for v in raw_vals])
                
                self.code_lines.append(f"{current_indent}{self.indent}sql = f'''INSERT INTO \"{table}\" VALUES ({val_str})'''")
                self.code_lines.append(f"{current_indent}{self.indent}cur.execute(sql)")
                self.code_lines.append(f"{current_indent}{self.indent}conn.commit()")
                self.code_lines.append(f"{current_indent}{self.indent}result_data = [{{'status': 'success', 'message': 'Row inserted'}}]")
    
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
            self.code_lines.append(f"{current_indent}result_data = [{{'status': 'success', 'message': 'Dropped {table}'}}]")
            
        elif op.op_type == "METADATA":
            self.code_lines.append(f"{current_indent}cur.execute(\"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'\")")
            self.code_lines.append(f"{current_indent}result_data = cur.fetchall()")

        if op.op_type in db_ops:
            self.code_lines.append(f"{self.indent}except psycopg2.Error as e:")
            self.code_lines.append(f"{self.indent}{self.indent}return [{{'status': 'error', 'message': f'Database Error: {{e.pgerror or str(e)}}'}}]")

        elif op.op_type == "SORT":
            col, ascending = op.params['column'], op.params['ascending']
            self.code_lines.append(f"{self.indent}result_data.sort(key=lambda x: get_val(x, '{col}') or '', reverse={not ascending})")
            
        elif op.op_type == "AGGREGATE":
            group_col = op.params.get('group_by')
            funcs = op.params.get('functions')
            g_col_name = group_col.name if hasattr(group_col, 'name') else group_col
            
            if g_col_name:
                self.code_lines.append(f"{self.indent}buckets = {{}}")
                self.code_lines.append(f"{self.indent}for row in result_data:")
                self.code_lines.append(f"{self.indent}{self.indent}key = get_val(row, '{g_col_name}')")
                self.code_lines.append(f"{self.indent}{self.indent}if key not in buckets: buckets[key] = []")
                self.code_lines.append(f"{self.indent}{self.indent}buckets[key].append(row)")
                self.code_lines.append(f"{self.indent}result_data = []")
                self.code_lines.append(f"{self.indent}for key, rows in buckets.items():")
                self.code_lines.append(f"{self.indent}{self.indent}res = {{'{g_col_name}': key}}")
                for f in funcs:
                    f_name = f.func.lower()
                    c_name = f.column.name
                    if f.func == 'COUNT':
                        self.code_lines.append(f"{self.indent}{self.indent}res['{f_name}'] = len(rows)")
                    elif f.func == 'SUM':
                        self.code_lines.append(f"{self.indent}{self.indent}res['{f_name}'] = sum(float(get_val(r, '{c_name}')) for r in rows if get_val(r, '{c_name}') is not None)")
                self.code_lines.append(f"{self.indent}{self.indent}result_data.append(res)")
            else:
                self.code_lines.append(f"{self.indent}res = {{}}")
                for f in funcs:
                    f_name = f.func.lower()
                    c_name = f.column.name
                    if f.func == 'COUNT':
                        self.code_lines.append(f"{self.indent}res['{f_name}'] = len(result_data)")
                    elif f.func == 'SUM':
                        self.code_lines.append(f"{self.indent}res['{f_name}'] = sum(float(get_val(r, '{c_name}')) for r in result_data if get_val(r, '{c_name}') is not None)")
                self.code_lines.append(f"{self.indent}result_data = [res]")
            
        elif op.op_type == "SET_OP":
            self._translate_op(op.params['left'])
            self.code_lines.append(f"{self.indent}left_side = result_data")
            self._translate_op(op.params['right'])
            self.code_lines.append(f"{self.indent}right_side = result_data")
            if op.params['op'] == "UNION":
                self.code_lines.append(f"{self.indent}result_data = [dict(t) for t in {{tuple(d.items()) for d in left_side + right_side}}]")
        
        elif op.op_type == "SUBQUERY_SCAN":
            self.code_lines.append(f"{self.indent}# Phase: SUBQUERY SCAN (Virtual Table Ready)")