# backend/codegen.py

class CodeGenerator:
    def __init__(self):
        self.code_lines = []
        self.indent = "    "

    def generate(self, optimized_plan):
        """Entry point for code generation."""
        self.code_lines = [
            "import psycopg2",
            "from psycopg2.extras import RealDictCursor",
            "",
            "def execute_compiled_query(conn_string):",
            f"{self.indent}conn = psycopg2.connect(conn_string)",
            f"{self.indent}cur = conn.cursor(cursor_factory=RealDictCursor)",
            ""
        ]
        
        # Traverse the plan and generate processing logic
        self._translate_op(optimized_plan)
        
        self.code_lines.extend([
            f"{self.indent}cur.close()",
            f"{self.indent}conn.close()",
            f"{self.indent}return result_data"
        ])
        
        return "\n".join(self.code_lines)

    def _translate_op(self, op):
        if not op:
            return

        # 1. Base Case: SCAN (The SQL part)
        if op.op_type == "SCAN":
            table = op.params['table']
            self.code_lines.append(f"{self.indent}# Phase: SCAN")
            # FIX: Added escaped double quotes around {table}
            self.code_lines.append(f"{self.indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{self.indent}result_data = cur.fetchall()")
            self.code_lines.append("")

        # 2. Recursive Step: Handle Source first
        if op.source:
            self._translate_op(op.source)

        # 3. Handle Logical Processing in Python
        if op.op_type == "FILTER":
            cond = op.params['condition']
            self.code_lines.append(f"{self.indent}# Phase: FILTER (WHERE {cond.left.name} {cond.op} {cond.right.value})")
            # Generate a list comprehension for the filter
            py_op = "==" if cond.op == "=" else cond.op
            val = f"'{cond.right.value}'" if isinstance(cond.right.value, str) else cond.right.value
            
            self.code_lines.append(
                f"{self.indent}result_data = [row for row in result_data if row['{cond.left.name}'] {py_op} {val}]"
            )

        elif op.op_type == "PROJECT":
            cols = op.params['columns']
            self.code_lines.append(f"{self.indent}# Phase: PROJECT (SELECT columns)")
            if "*" in cols:
                return
                
            col_list = [f"'{c}'" for c in cols if isinstance(c, str)]
            self.code_lines.append(
                f"{self.indent}result_data = [{{k: row[k] for k in [{', '.join(col_list)}]}} for row in result_data]"
            )

        elif op.op_type == "JOIN":
            table = op.params['table']
            self.code_lines.append(f"{self.indent}# Phase: JOIN ({table})")
            self.code_lines.append(f"{self.indent}cur.execute('SELECT * FROM \"{table}\"')")
            self.code_lines.append(f"{self.indent}join_table_data = cur.fetchall()")
            # Nested Loop Join implementation (Educational and Explicit)
            self.code_lines.append(f"{self.indent}joined_results = []")
            self.code_lines.append(f"{self.indent}for r1 in result_data:")
            self.code_lines.append(f"{self.indent}{self.indent}for r2 in join_table_data:")
            self.code_lines.append(f"{self.indent}{self.indent}{self.indent}joined_results.append({{**r1, **r2}})")
            self.code_lines.append(f"{self.indent}result_data = joined_results")