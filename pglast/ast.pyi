from pglast.enums.nodes import JoinType

class Node:
    pass

class A_Star(Node):
    pass

class ColumnRef(Node):
    fields: tuple[Node, ...]

class RawStmt(Node):
    stmt: Node
    stmt_len: int
    stmt_location: int

class ResTarget(Node):
    location: int
    name: str | None
    val: Node

class Alias(Node):
    aliasname: str

class RangeVar(Node):
    alias: Alias | None
    relname: str

class JoinExpr(Node):
    alias: Alias
    jointype: JoinType
    larg: Node
    rarg: Node

class SelectStmt(Node):
    targetList: tuple[ResTarget, ...]
    fromClause: tuple[Node, ...] | None

class RangeSubselect(Node):
    lateral: bool
    subquery: Node
    alias: Alias

class InsertStmt(Node):
    relation: RangeVar
    cols: tuple[ResTarget, ...]
