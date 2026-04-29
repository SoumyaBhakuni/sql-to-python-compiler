from models import (
    SelectNode, InsertNode, DropTableNode, BinaryOpNode, 
    IdentifierNode, AggregateNode, UpdateNode, DeleteNode, SetOpNode
)

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
            
        # Handle SET OPERATIONS recursively (e.g., UNION)
        if isinstance(node, SetOpNode):
            self.analyze(node.left)
            self.analyze(node.right)
            return True
            
        # Dispatch to specific validators based on Node Type
        if isinstance(node, SelectNode):
            return self._validate_select(node)
        elif isinstance(node, InsertNode):
            return self._validate_insert(node)
        elif isinstance(node, UpdateNode):
            return self._validate_update(node)
        elif isinstance(node, DeleteNode):
            return self._validate_delete(node)
        elif getattr(node, '__class__', None).__name__ == 'CreateNode':
            return self._validate_create(node)
        elif isinstance(node, DropTableNode):
            return self._validate_drop(node)
        
        return True

    def _get_name(self, node):
        """Helper to extract the string name from an IdentifierNode or raw string."""
        if isinstance(node, IdentifierNode):
            return node.name
        return str(node)

    def _validate_select(self, node):
        available_columns = set()

        # 1. Handle Subqueries (Recursion!) vs Standard Table
        if isinstance(node.from_table, SelectNode):
            self.analyze(node.from_table)  # Recurse into the inner query
            
            # Extract available columns from the subquery's projection so the outer query can validate
            for proj in node.from_table.projections:
                if proj == "*":
                    available_columns.add("*")
                else:
                    if isinstance(proj, AggregateNode):
                        available_columns.add(self._get_name(proj.column))
                    else:
                        available_columns.add(self._get_name(proj))
        
        elif node.from_table:
            # Standard Table Validation
            if node.from_table not in self.schema:
                raise ValueError(f"Semantic Error: Table '{node.from_table}' not found in schema.")

            # Add columns from the base table
            for col in self.schema[node.from_table]:
                available_columns.add(col)
                available_columns.add(f"{node.from_table}.{col}")

        # 2. Add columns from any JOINed tables
        if hasattr(node, 'joins') and node.joins:
            for join in node.joins:
                if join.table not in self.schema:
                    raise ValueError(f"Semantic Error: Joined table '{join.table}' does not exist.")
                for col in self.schema[join.table]:
                    available_columns.add(col)
                    available_columns.add(f"{join.table}.{col}")

        # 3. Validate Projections (The SELECT list)
        if "*" not in available_columns: # Skip strict check if subquery returned *
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
        if node.where and "*" not in available_columns:
            self._check_expression(node.where, available_columns)
            
        return True

    def _check_expression(self, expr, available_cols):
        """Recursively check identifiers in WHERE conditions and operations."""
        if isinstance(expr, BinaryOpNode):
            self._check_expression(expr.left, available_cols)
            self._check_expression(expr.right, available_cols)
        elif isinstance(expr, IdentifierNode):
            # Check for 'Table.Column' if table is specified, otherwise check 'Column'
            search_name = f"{expr.table}.{expr.name}" if getattr(expr, 'table', None) else expr.name
            
            if search_name not in available_cols and expr.name not in available_cols:
                raise ValueError(f"Semantic Error: Unknown identifier '{search_name}' in WHERE clause.")

    def _validate_insert(self, node):
        if node.table not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.table}' not found.")
        return True

    def _validate_drop(self, node):
        table_name = getattr(node, 'table_name', getattr(node, 'table', None))
        if table_name and table_name not in self.schema:
            raise ValueError(f"Semantic Error: Table '{table_name}' does not exist.")
        return True
    
    def _validate_update(self, node):
        """Ensure columns being updated exist in the target table."""
        if node.table not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.table}' not found for UPDATE.")
        
        table_cols = self.schema[node.table]
        for assign in node.assignments:
            if assign['column'] not in table_cols:
                raise ValueError(f"Semantic Error: Column '{assign['column']}' does not exist in '{node.table}'.")
        return True

    def _validate_delete(self, node):
        if node.table not in self.schema:
            raise ValueError(f"Semantic Error: Table '{node.table}' not found for DELETE.")
        return True

    def _validate_create(self, node):
        """Prevent duplicate table creation and validate basic types."""
        table_name = getattr(node, 'table_name', None)
        if table_name and table_name in self.schema:
            raise ValueError(f"Semantic Error: Table '{table_name}' already exists.")
        
        valid_types = {'INT', 'TEXT', 'FLOAT', 'VARCHAR', 'BOOLEAN', 'INTEGER', 'SERIAL', 'DATE', 'TIMESTAMP', 'TIMESTAMP WITH TIME ZONE'}
        for col in getattr(node, 'columns', []):
            if col['type'].upper() not in valid_types:
                raise ValueError(f"Semantic Error: Unsupported data type '{col['type']}' for column '{col['name']}'.")
        return True