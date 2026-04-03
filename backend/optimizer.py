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
        if not op or not op.source:
            return op

        op.source = self._push_down_predicates(op.source)

        # CORRECT LOGIC: Push FILTER down BELOW PROJECT
        # If current is FILTER and source is PROJECT, swap them.
        if op.op_type == "FILTER" and op.source.op_type == "PROJECT":
            filter_op = op
            project_op = op.source
            
            # Swap: FILTER now points to SCAN, PROJECT now points to FILTER
            new_source = project_op.source # The SCAN
            filter_op.source = new_source
            project_op.source = filter_op
            
            # Return PROJECT as the new top node
            return project_op

        return op