# backend/optimizer.py
from planner import RelationalOp

class QueryOptimizer:
    def optimize(self, plan):
        """Entry point for logical optimization."""
        if not isinstance(plan, RelationalOp):
            return plan
        
        # Rule 1: Predicate Pushdown (Move FILTER below JOIN/PROJECT)
        optimized_plan = self._push_down_predicates(plan)
        
        return optimized_plan

    def _push_down_predicates(self, op):
        """Recursively moves FILTER nodes as deep as possible in the tree."""
        if not op or not op.source:
            return op

        # Recurse down to the bottom first
        op.source = self._push_down_predicates(op.source)

        # RULE: Push FILTER below JOIN
        if op.op_type == "FILTER" and op.source.op_type == "JOIN":
            filter_op = op
            join_op = op.source
            
            # If the filter doesn't reference the joined table, push it down
            if self._can_push_to_source(filter_op.params['condition'], join_op.params['table']):
                filter_op.source = join_op.source
                join_op.source = filter_op
                return join_op

        # RULE: Push FILTER below PROJECT
        if op.op_type == "FILTER" and op.source.op_type == "PROJECT":
            filter_op = op
            project_op = op.source
            
            new_source = project_op.source
            filter_op.source = new_source
            project_op.source = filter_op
            
            return project_op

        return op

    def _can_push_to_source(self, condition, joined_table):
        """Returns True if the condition does not reference the joined table."""
        # Check if this node is an Identifier belonging to the joined table
        if hasattr(condition, 'table') and condition.table == joined_table:
            return False
        
        # Recursively check binary operations (AND/OR/EQUALS)
        if hasattr(condition, 'left') and hasattr(condition, 'right'):
            return self._can_push_to_source(condition.left, joined_table) and \
                   self._can_push_to_source(condition.right, joined_table)
        
        return True