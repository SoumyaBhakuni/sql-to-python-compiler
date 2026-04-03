# backend/optimizer.py
from planner import RelationalOp

class QueryOptimizer:
    def optimize(self, plan):
        """Entry point for logical optimization."""
        if not isinstance(plan, RelationalOp):
            return plan
        
        # Rule 1: Predicate Pushdown (Move FILTER below JOIN/PROJECT)
        optimized_plan = self._push_down_predicates(plan)
        
        # Rule 2: Projection Pruning (Optional: Only fetch needed columns)
        # For our PBL, we will focus primarily on Pushdown.
        
        return optimized_plan

    def _push_down_predicates(self, op):
        """
        Recursively looks for FILTER nodes and tries to move them 
        deeper into the tree (closer to the SCAN).
        """
        if not op or not op.source:
            return op

        # Recursive call to optimize the source first (Bottom-Up)
        op.source = self._push_down_predicates(op.source)

        # Logic: If current is PROJECT and source is FILTER, swap them.
        # This ensures we filter rows before we throw away columns.
        if op.op_type == "PROJECT" and op.source.op_type == "FILTER":
            filter_op = op.source
            project_op = op
            
            # Swap: PROJECT points to FILTER's source, FILTER points to PROJECT
            new_source = filter_op.source
            filter_op.source = project_op
            project_op.source = new_source
            
            # Return the filter as the new top node
            return filter_op

        return op