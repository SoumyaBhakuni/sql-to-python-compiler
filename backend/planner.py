# backend/planner.py

class RelationalOp:
    """A single logical operation in Relational Algebra."""
    def __init__(self, op_type, source=None, params=None):
        self.op_type = op_type  # SCAN, JOIN, FILTER, PROJECT, AGGREGATE, SORT, SET_OP, SUBQUERY_SCAN
        self.source = source    
        self.params = params    

    def to_dict(self):
        """Serialization for the React Visualizer's 'Inspector Modal'."""
        # Fix: Recursively convert nested RelationalOp objects within params
        clean_params = {}
        if self.params:
            for k, v in self.params.items():
                if isinstance(v, RelationalOp):
                    clean_params[k] = v.to_dict()
                elif isinstance(v, list):
                    # Handle lists of nodes if necessary
                    clean_params[k] = [item.to_dict() if isinstance(item, RelationalOp) else item for item in v]
                else:
                    clean_params[k] = v

        return {
            "op": self.op_type,
            "params": clean_params,
            "source": self.source.to_dict() if self.source else None
        }

# Replace your QueryPlanner class in backend/planner.py with this:

class QueryPlanner:
    def _find_aggregates(self, node):
        """Recursively hunts for AggregateNodes hidden inside math or aliases."""
        aggs = []
        if not node: return aggs
        if isinstance(node, list):
            for n in node: aggs.extend(self._find_aggregates(n))
        elif node.__class__.__name__ == "AggregateNode":
            aggs.append(node)
        elif node.__class__.__name__ == "AliasNode":
            aggs.extend(self._find_aggregates(node.expr))
        elif node.__class__.__name__ == "BinaryOpNode":
            aggs.extend(self._find_aggregates(node.left))
            aggs.extend(self._find_aggregates(node.right))
        return aggs

    def create_plan(self, ast_node):
        """Converts an AST node into a Relational Algebra Tree."""
        if isinstance(ast_node, RelationalOp): return ast_node

        if ast_node.__class__.__name__ == "SetOpNode":
            return RelationalOp("SET_OP", params={
                "op": ast_node.op,
                "left": self.create_plan(ast_node.left),
                "right": self.create_plan(ast_node.right)
            })

        node_type = ast_node.__class__.__name__
        
        # [ ... Keep your INSERT, DELETE, UPDATE, CREATE, DROP logic ... ]
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
        if hasattr(ast_node, 'from_table') and ast_node.from_table.__class__.__name__ == "SelectNode":
            plan = RelationalOp("SUBQUERY_SCAN", source=self.create_plan(ast_node.from_table))
        else:
            plan = RelationalOp("SCAN", params={"table": ast_node.from_table})

        # --- 2. JOIN: Combine Tables ---
        if hasattr(ast_node, 'joins'):
            for join in ast_node.joins:
                plan = RelationalOp("JOIN", source=plan, params={
                    "type": join.join_type, "table": join.table, "on": join.on_condition
                })

        # --- 3. FILTER: The WHERE Clause ---
        if hasattr(ast_node, 'where') and ast_node.where:
            plan = RelationalOp("FILTER", source=plan, params={"condition": ast_node.where})

        # --- 4. AGGREGATE/GROUP: The GROUP BY Clause ---
        # THE FIX: Recursively extract ALL aggregates from projections and HAVING
        all_aggs = self._find_aggregates(ast_node.projections)
        if hasattr(ast_node, 'group_by') and ast_node.group_by and ast_node.group_by.get('having'):
            all_aggs.extend(self._find_aggregates(ast_node.group_by['having']))
            
        # Deduplicate aggregates so we don't calculate COUNT(studentId) twice
        unique_aggs = []
        seen = set()
        for a in all_aggs:
            c_name = a.column.name if hasattr(a.column, 'name') else str(a.column)
            key = f"{a.func}_{c_name}"
            if key not in seen:
                seen.add(key)
                unique_aggs.append(a)

        if (hasattr(ast_node, 'group_by') and ast_node.group_by) or unique_aggs:
            plan = RelationalOp("AGGREGATE", source=plan, params={
                "columns": ast_node.group_by['columns'] if ast_node.group_by else [],
                "having": ast_node.group_by['having'] if ast_node.group_by else None,
                "functions": unique_aggs
            })
    
        # --- 5. ROOT: The Projection ---
        plan = RelationalOp("PROJECT", source=plan, params={"columns": ast_node.projections})
        
        # --- 6. SORT: The ORDER BY Clause ---
        if hasattr(ast_node, 'order_by') and ast_node.order_by:
            plan = RelationalOp("SORT", source=plan, params=ast_node.order_by)

        # --- 7. LIMIT: The LIMIT Clause --- (ADD THIS BLOCK)
        if hasattr(ast_node, 'limit') and ast_node.limit is not None:
            plan = RelationalOp("LIMIT", source=plan, params={"value": ast_node.limit})
            
        return plan