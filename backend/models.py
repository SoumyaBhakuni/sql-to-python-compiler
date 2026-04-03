from typing import List, Optional, Any, Union

class Node:
    """Base class for all Abstract Syntax Tree nodes."""
    def to_dict(self):
        """Helper for JSON serialization for the React Visualizer."""
        data = {"node_type": self.__class__.__name__}
        for k, v in self.__dict__.items():
            if hasattr(v, 'to_dict'):
                data[k] = v.to_dict()
            elif isinstance(v, list):
                data[k] = [i.to_dict() if hasattr(i, 'to_dict') else i for i in v]
            else:
                data[k] = v
        return data

class ExpressionNode(Node): pass

class LiteralNode(ExpressionNode):
    def __init__(self, value: Any, data_type: str):
        self.value = value
        self.data_type = data_type # 'INT', 'TEXT', 'FLOAT'

class IdentifierNode(ExpressionNode):
    def __init__(self, name: str, table: Optional[str] = None):
        self.name = name
        self.table = table

class BinaryOpNode(ExpressionNode):
    def __init__(self, left, op: str, right):
        self.left = left
        self.op = op
        self.right = right

class AggregateNode(ExpressionNode):
    def __init__(self, func: str, column: Union[str, IdentifierNode]):
        self.func = func.upper()
        self.column = column

class JoinNode(Node):
    def __init__(self, join_type: str, table: str, on_condition: Optional[Node] = None):
        self.join_type = join_type.upper()
        self.table = table
        self.on_condition = on_condition

class SelectNode(Node):
    def __init__(self, projections, from_table, joins=None, where=None, group_by=None, having=None):
        self.projections = projections # List of strings, Identifiers, or Aggregates
        self.from_table = from_table
        self.joins = joins or []
        self.where = where
        self.group_by = group_by
        self.having = having

class InsertNode(Node):
    def __init__(self, table: str, values: List[Any]):
        self.table = table
        self.values = values

class CreateTableNode(Node):
    def __init__(self, table_name: str, columns: List[dict]):
        self.table_name = table_name
        self.columns = columns # [{'name': str, 'type': str}]

class DropTableNode(Node):
    def __init__(self, table_name: str):
        self.table_name = table_name