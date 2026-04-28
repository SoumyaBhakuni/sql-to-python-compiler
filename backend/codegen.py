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
        """Recursively converts AST nodes into Null-safe Python strings."""
        if hasattr(node, 'name'):
           return f"get_val(row, '{node.name}')"
    
        if hasattr(node, 'value'):
            return repr(node.value)

        if hasattr(node, 'left') and hasattr(node, 'right'):
            left_part = self._build_python_expr(node.left)
            right_part = self._build_python_expr(node.right)
        
            op_map = {'=': '==', 'AND': 'and', 'OR': 'or', 'NEQ': '!='}
            py_op = op_map.get(node.op.upper(), node.op)
        
            # Null-safety check for comparison operators
            if py_op in ['<', '>', '<=', '>=', '==', '!=']:
               return f"({left_part} is not None and {left_part} {py_op} {right_part})"
        
            return f"({left_part} {py_op} {right_part})"
    
        return "True"

    def _translate_op(self, op):
        if not op:
            return

        if hasattr(op, 'source') and op.source:
            self._translate_op(op.source)

        if op.op_type == "SCAN":
            table = op.params['table']
            self.code_lines.append(f"{self.indent}# Phase: SCAN \"{table}\"")
            self.code_lines.append(f"{self.indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{self.indent}result_data = cur.fetchall()")

        elif op.op_type == "FILTER":
            cond = op.params['condition']
            py_expression = self._build_python_expr(cond)
            self.code_lines.append(f"{self.indent}# Phase: FILTER (Complex Expression)")
            self.code_lines.append(
                f"{self.indent}result_data = [row for row in result_data if {py_expression}]"
            )

        elif op.op_type == "PROJECT":
            cols = op.params['columns']
            self.code_lines.append(f"{self.indent}# Phase: PROJECT & AGGREGATE")
        
            has_aggregates = any(hasattr(c, 'func') for c in cols)
        
            if has_aggregates:
                self.code_lines.append(f"{self.indent}agg_results = {{}}")
                for col in cols:
                    if hasattr(col, 'func'):
                        func = col.func.upper()
                        c_name = col.column.name
                        
                        # Key name standardized to lowercase to match standard SQL output format
                        key_name = func.lower() 
                        
                        if func == 'COUNT':
                            self.code_lines.append(f"{self.indent}agg_results['{key_name}'] = len(result_data)")
                        elif func == 'SUM':
                            self.code_lines.append(
                                f"{self.indent}agg_results['sum'] = sum("
                                f"float(get_val(r, '{c_name}')) for r in result_data "
                                f"if get_val(r, '{c_name}') is not None)"
                            )
                self.code_lines.append(f"{self.indent}result_data = [agg_results]")
            else:
                col_names = [c.name if hasattr(c, 'name') else str(c) for c in cols]
                if "*" in col_names:
                    self.code_lines.append(f"{self.indent}# Keep all columns (SELECT *)")
                else:
                    col_list = ", ".join([f"'{c}'" for c in col_names])
                    self.code_lines.append(
                        f"{self.indent}result_data = [{{c: get_val(row, c) for c in [{col_list}]}} for row in result_data]"
                    )

        elif op.op_type == "JOIN":
            table = op.params['table']
            on_cond = op.params['on']
            self.code_lines.append(f"{self.indent}# Phase: JOIN \"{table}\"")
            self.code_lines.append(f"{self.indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{self.indent}join_table_data = cur.fetchall()")
            self.code_lines.append(f"{self.indent}joined_results = []")
            
            left_key = on_cond.left.name
            right_key = on_cond.right.name
            
            self.code_lines.append(f"{self.indent}for r1 in result_data:")
            self.code_lines.append(f"{self.indent}{self.indent}for r2 in join_table_data:")
            self.code_lines.append(
                f"{self.indent}{self.indent}{self.indent}if get_val(r1, '{left_key}') == get_val(r2, '{right_key}'):"
            )
            self.code_lines.append(
                f"{self.indent}{self.indent}{self.indent}{self.indent}joined_results.append({{**r1, **r2}})"
            )
            self.code_lines.append(f"{self.indent}result_data = joined_results")