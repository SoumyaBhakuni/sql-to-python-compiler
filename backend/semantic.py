from models import SelectNode, InsertNode, DropTableNode, BinaryOpNode, IdentifierNode, AggregateNode

class SemanticAnalyzer:
    def __init__(self, schema):
        """
        schema: A dictionary of table names and their lists of columns.
        Example: {'Students': ['studentId', 'name', 'year'], 'Courses': [...]}
        """
        self.schema = schema

    def analyze(self, node):
        if not node:
            return True
            
        node_type = node.__class__.__name__
        
        # Dispatch to specific validators
        if node_type == "SelectNode":
            return self._validate_select(node)
        elif node_type == "InsertNode":
            return self._validate_insert(node)
        elif node_type == "DropTableNode":
            return self._validate_drop(node)
        
        return True

    def _get_name(self, node):
        """Helper to extract the string name from an IdentifierNode or raw string."""
        if isinstance(node, IdentifierNode):
            return node.name
        return str(node)

    def _validate_select(self, node):
        # 1. Validate 'FROM' Table
        if node.from_table not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.from_table}' not found in schema.")

        # 2. Build the context of available columns
        # We store them as 'table.column' and 'column' for easy lookup
        available_columns = set()
        
        # Add columns from base table
        for col in self.schema[node.from_table]:
            available_columns.add(col)
            available_columns.add(f"{node.from_table}.{col}")

        # Add columns from JOINs
        for join in node.joins:
            if join.table not in self.schema:
                raise ValueError(f"Semantic Error: Joined table '{join.table}' does not exist.")
            for col in self.schema[join.table]:
                available_columns.add(col)
                available_columns.add(f"{join.table}.{col}")

        # 3. Validate Projections
        for proj in node.projections:
            if proj == "*":
                continue
            
            # Handle AggregateNode vs IdentifierNode
            if isinstance(proj, AggregateNode):
                col_name = self._get_name(proj.column)
            else:
                col_name = self._get_name(proj)
            
            if col_name not in available_columns:
                raise ValueError(f"Semantic Error: Column '{col_name}' is not available in the current context.")

        # 4. Validate WHERE clause
        if node.where:
            self._check_expression(node.where, available_columns)
            
        return True

    def _check_expression(self, expr, available_cols):
        """Recursively check identifiers in WHERE conditions."""
        if isinstance(expr, BinaryOpNode):
            self._check_expression(expr.left, available_cols)
            self._check_expression(expr.right, available_cols)
        elif isinstance(expr, IdentifierNode):
            # Check for 'table.column' if table is provided, else check 'column'
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