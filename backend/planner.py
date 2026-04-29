# backend/planner.py (Updated with Feature 4 & 5 Logic)

class RelationalOp:
    """A single logical operation in Relational Algebra."""
    def __init__(self, op_type, source=None, params=None):
        self.op_type = op_type  # SCAN, JOIN, FILTER, PROJECT, AGGREGATE, SORT, SET_OP, SUBQUERY_SCAN
        self.source = source    
        self.params = params    

    def to_dict(self):
        """Serialization for the React Visualizer's 'Inspector Modal'."""
        return {
            "op": self.op_type,
            "params": self.params,
            "source": self.source.to_dict() if self.source else None
        }

class QueryPlanner:
    def create_plan(self, ast_node):
        """Converts an AST node into a Relational Algebra Tree."""
        
        # --- NEW: Set Operations (UNION, INTERSECT, EXCEPT) ---
        # If the root is a SetOpNode, we recursively plan both sides
        if ast_node.__class__.__name__ == "SetOpNode":
            return RelationalOp("SET_OP", params={
                "op": ast_node.op,
                "left": self.create_plan(ast_node.left),
                "right": self.create_plan(ast_node.right)
            })

        node_type = ast_node.__class__.__name__
        
        # Handle non-SELECT DDL/DML operations
        if node_type == "InsertNode":
            return RelationalOp("INSERT", params={'table': ast_node.table, 'values': ast_node.values})
        elif node_type == "DeleteNode":
            return RelationalOp("DELETE", params={'table': ast_node.table, 'condition': ast_node.where})
        elif node_type == "UpdateNode":
            return RelationalOp("UPDATE", params={'table': ast_node.table, 'assigns': ast_node.assignments, 'condition': ast_node.where})
        elif node_type == "CreateTableNode":
            return RelationalOp("CREATE", params={'table': ast_node.table_name, 'columns': ast_node.columns})
        elif node_type == "DropTableNode":
            return RelationalOp("DROP", params={'table': ast_node.table_name})
        elif node_type == "ShowTablesNode":
            return RelationalOp("METADATA", params={"type": "SHOW_TABLES"})

        # --- 1. LEAF: Table Scan or SUBQUERY ---
        # Check if the source is another SELECT statement (Subquery) or a raw table
        if hasattr(ast_node, 'from_table') and ast_node.from_table.__class__.__name__ == "SelectNode":
            source_plan = self.create_plan(ast_node.from_table)
            plan = RelationalOp("SUBQUERY_SCAN", source=source_plan)
        else:
            plan = RelationalOp("SCAN", params={"table": ast_node.from_table})

        # --- 2. JOIN: Combine Tables ---
        for join in ast_node.joins:
            plan = RelationalOp("JOIN", source=plan, params={
                "type": join.join_type,
                "table": join.table,
                "on": join.on_condition
            })

        # --- 3. FILTER: The WHERE Clause ---
        if ast_node.where:
            plan = RelationalOp("FILTER", source=plan, params={"condition": ast_node.where})

        # --- 4. AGGREGATE/GROUP: The GROUP BY Clause ---
        if ast_node.group_by or any(hasattr(p, 'func') for p in ast_node.projections):
            plan = RelationalOp("AGGREGATE", source=plan, params={
                "group_by": ast_node.group_by['column'] if ast_node.group_by else None,
                "having": ast_node.group_by['having'] if ast_node.group_by else None,
                "functions": [p for p in ast_node.projections if hasattr(p, 'func')]
            })
    
        # --- 5. ROOT: The Projection ---
        plan = RelationalOp("PROJECT", source=plan, params={"columns": ast_node.projections})
        
        # --- 6. SORT: The ORDER BY Clause ---
        if hasattr(ast_node, 'order_by') and ast_node.order_by:
            plan = RelationalOp("SORT", source=plan, params=ast_node.order_by)
            
        return plan