# backend/planner.py

class RelationalOp:
    """A single logical operation in Relational Algebra."""
    def __init__(self, op_type, source=None, params=None):
        self.op_type = op_type  # SCAN, JOIN, FILTER, PROJECT, AGGREGATE
        self.source = source    # The operation that feeds into this one (Unary/Binary)
        self.params = params    # Metadata like table name, condition, or columns

    def to_dict(self):
        """Serialization for the React Visualizer's 'Inspector Modal'."""
        return {
            "op": self.op_type,
            "params": self.params,
            "source": self.source.to_dict() if self.source else None
        }

class QueryPlanner:
    def create_plan(self, ast_node):
        """Converts a SelectNode AST into a Relational Algebra Tree."""
        node_type = ast_node.__class__.__name__
        
        if node_type != "SelectNode":
            # For INSERT/CREATE/DROP, the 'Plan' is just the AST itself.
            return ast_node

        # --- 1. LEAF: Table Scan ---
        # The foundation of every SELECT is scanning the base table.
        plan = RelationalOp("SCAN", params={"table": ast_node.from_table})

        # --- 2. JOIN: Combine Tables ---
        # We wrap the SCAN in JOIN operations if they exist.
        for join in ast_node.joins:
            plan = RelationalOp("JOIN", source=plan, params={
                "type": join.join_type,
                "table": join.table,
                "on": join.on_condition
            })

        # --- 3. FILTER: The WHERE Clause ---
        # Logically, we filter rows after joining/scanning.
        if ast_node.where:
            plan = RelationalOp("FILTER", source=plan, params={"condition": ast_node.where})

        # --- 4. AGGREGATE/GROUP: The GROUP BY Clause ---
        if ast_node.group_by or any(hasattr(p, 'func') for p in ast_node.projections):
            plan = RelationalOp("AGGREGATE", source=plan, params={
                "group_by": ast_node.group_by,
                "functions": [p for p in ast_node.projections if hasattr(p, 'func')]
            })

        # --- 5. ROOT: The Projection ---
        # Finally, we pick only the columns requested in the SELECT.
        plan = RelationalOp("PROJECT", source=plan, params={"columns": ast_node.projections})

        return plan