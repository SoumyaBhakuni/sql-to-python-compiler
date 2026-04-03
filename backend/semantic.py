from models import SelectNode, InsertNode, DropTableNode, BinaryOpNode, IdentifierNode, AggregateNode

class SemanticAnalyzer:
    def __init__(self, schema):
        """
        schema: Dynamic dictionary fetched from DatabaseManager.
        Format: {'Students': ['studentId', 'name', ...], 'Clubs': [...]}
        """
        self.schema = schema

    def analyze(self, node):
        """Recursive traversal of the AST to validate logic."""
        if not node:
            return True
            
        # Dispatch to specific validators based on Node Type
        if isinstance(node, SelectNode):
            return self._validate_select(node)
        elif isinstance(node, InsertNode):
            return self._validate_insert(node)
        elif isinstance(node, DropTableNode):
            return self._validate_drop(node)
        
        return True

    def _get_name(self, node):
        """Helper to extract the string name from an IdentifierNode or raw string."""
        if isinstance(node, IdentifierNode):
            return node.name
        return str(node)

    def _validate_select(self, node):
        # 1. Validate 'FROM' Table (Case-Sensitive for PascalCase)
        if node.from_table not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.from_table}' not found in schema.")

        # 2. Build the context of available columns for this query
        # We store both 'column' and 'Table.column' for namespace resolution
        available_columns = set()
        
        # Add columns from the base table
        for col in self.schema[node.from_table]:
            available_columns.add(col)
            available_columns.add(f"{node.from_table}.{col}")

        # Add columns from any JOINed tables
        for join in node.joins:
            if join.table not in self.schema:
                raise ValueError(f"Semantic Error: Joined table '{join.table}' does not exist.")
            for col in self.schema[join.table]:
                available_columns.add(col)
                available_columns.add(f"{join.table}.{col}")

        # 3. Validate Projections (The SELECT list)
        for proj in node.projections:
            if proj == "*":
                continue
            
            # Extract name whether it's a raw ID, IdentifierNode, or Aggregate
            if isinstance(proj, AggregateNode):
                col_name = self._get_name(proj.column)
            else:
                col_name = self._get_name(proj)
            
            # Check against the available column context
            if col_name not in available_columns:
                # Try a case-insensitive check to provide a helpful hint
                suggestions = [c for c in available_columns if c.lower() == col_name.lower()]
                error_msg = f"Semantic Error: Column '{col_name}' is not available."
                if suggestions:
                    error_msg += f" Did you mean '{suggestions[0]}'?"
                raise ValueError(error_msg)

        # 4. Validate WHERE clause (if exists)
        if node.where:
            self._check_expression(node.where, available_columns)
            
        return True

    def _check_expression(self, expr, available_cols):
        """Recursively check identifiers in WHERE conditions and operations."""
        if isinstance(expr, BinaryOpNode):
            self._check_expression(expr.left, available_cols)
            self._check_expression(expr.right, available_cols)
        elif isinstance(expr, IdentifierNode):
            # Check for 'Table.Column' if table is specified, otherwise check 'Column'
            search_name = f"{expr.table}.{expr.name}" if expr.table else expr.name
            
            if search_name not in available_cols and expr.name not in available_cols:
                raise ValueError(f"Semantic Error: Unknown identifier '{search_name}' in WHERE clause.")

    def _validate_insert(self, node):
        if node.table not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.table}' not found.")
        return True

    def _validate_drop(self, node):
        if node.table_name not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.table_name}' does not exist.")
        return True