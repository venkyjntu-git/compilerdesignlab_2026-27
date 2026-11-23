"""
TinyCStr Level 2 + Level 3 -- Semantic Analysis / Type Checker.

WEEK 8 ADDITIONS (flagged, provided -- not this week's exercise):
  1. Name lookup is now TWO-level: a function's LOCAL symbol table
     first, then the program's GLOBAL symbol table (Stage 3b's global
     declarations) -- see lookup(). A local with the same name as a
     global hides it, as in C.
  2. Three new statement kinds: If, While, Block. A condition is checked
     exactly like the ternary's condition already was (must be numeric:
     int/char/double -- a string is not a truth value), and each branch,
     loop body and block member is checked recursively with check_stmt().

FULLY IMPLEMENTED since Week 7 -- this is Week 6's exercise, now carried
forward as infrastructure for Week 7's codegen.

WEEK 7 ADDITION (flagged, small): check_expr() now also stamps
`node.result_type` on whatever node it returns, for EVERY expression
node -- Const, Var, BinOp, RelOp, Cast, Ternary alike. This didn't
matter for Week 6 (which only needed the RETURNED type, to
keep checking the rest of the tree) but Week 7's tac_generator.py needs
to know each node's resolved type when it walks the AST a second time
to emit typed 3AC, without re-running type inference from scratch.
Reading `node.result_type` directly is that lookup.
"""
from ast_nodes import Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary, If, While, Block
from SymbolTable import DataType
from type_rules import is_numeric, promote, SemanticError


class TypeChecker:
    def __init__(self, global_symbol_table=None):
        self.errors = []
        self.global_symbol_table = global_symbol_table  # WEEK 8

    def lookup(self, name):
        """WEEK 8: local scope first, then global scope; None if in neither."""
        entry = self.symbol_table.getSymbol(name)
        if entry is None and self.global_symbol_table is not None:
            entry = self.global_symbol_table.getSymbol(name)
        return entry

    def error(self, message, lineno):
        self.errors.append(SemanticError(message, lineno))

    def check_function(self, function):
        self.symbol_table = function.getLocalSymbolTable()
        checked_stmts = []
        for stmt in function.getStatementsAstList():
            checked_stmts.append(self.check_stmt(stmt))
        function.setStatementsAstList(checked_stmts)
        return self.errors

    def check_stmt(self, stmt):
        if isinstance(stmt, Assign):
            return self.check_assign_stmt(stmt)
        elif isinstance(stmt, Print):
            return self.check_print_stmt(stmt)
        elif isinstance(stmt, If):          # WEEK 8
            return self.check_if_stmt(stmt)
        elif isinstance(stmt, While):       # WEEK 8
            return self.check_while_stmt(stmt)
        elif isinstance(stmt, Block):       # WEEK 8
            stmt.stmts = [self.check_stmt(s) for s in stmt.stmts]
            return stmt
        else:
            raise ValueError(f"unexpected statement type: {type(stmt)}")

    def check_expr(self, node):
        if isinstance(node, Const):
            result_node, result_type = node, node.type
        elif isinstance(node, Var):
            result_node, result_type = self.check_var(node)
        elif isinstance(node, BinOp):
            result_node, result_type = self.check_binop(node)
        elif isinstance(node, RelOp):
            result_node, result_type = self.check_relop(node)
        elif isinstance(node, Cast):
            result_node, result_type = self.check_cast(node)
        elif isinstance(node, Ternary):
            result_node, result_type = self.check_ternary(node)
        else:
            raise ValueError(f"unexpected expr node type: {type(node)}")
        result_node.result_type = result_type  # WEEK 7 addition
        return result_node, result_type

    def check_var(self, node):
        entry = self.lookup(node.name)
        if entry is None:
            self.error(f"undeclared variable '{node.name}'", node.lineno)
            return node, DataType.INT
        return node, entry.getDataType()

    def _maybe_cast(self, child, child_type, target_type, lineno):
        if child_type != target_type:
            # WEEK 8/9 FIX: stamp the inserted Cast's own result_type. Without it,
            # a MIXED comparison such as `i < 2.5` crashed 3AC generation, because
            # tac_generator reads node.left.result_type and node.left is this Cast.
            cast = Cast(target_type, child, lineno=lineno)
            cast.result_type = target_type
            return cast
        return child

    def check_binop(self, node):
        left, left_type = self.check_expr(node.left)
        right, right_type = self.check_expr(node.right)
        if not is_numeric(left_type) or not is_numeric(right_type):
            self.error(f"arithmetic operator '{node.op}' not supported for type "
                       f"{left_type if not is_numeric(left_type) else right_type}", node.lineno)
            node.left, node.right = left, right
            return node, DataType.INT
        result_type = promote(left_type, right_type)
        node.left = self._maybe_cast(left, left_type, result_type, node.lineno)
        node.right = self._maybe_cast(right, right_type, result_type, node.lineno)
        return node, result_type

    def check_relop(self, node):
        left, left_type = self.check_expr(node.left)
        right, right_type = self.check_expr(node.right)
        if is_numeric(left_type) and is_numeric(right_type):
            result_type = promote(left_type, right_type)
            node.left = self._maybe_cast(left, left_type, result_type, node.lineno)
            node.right = self._maybe_cast(right, right_type, result_type, node.lineno)
        elif left_type == DataType.STRING and right_type == DataType.STRING:
            node.left, node.right = left, right
        else:
            self.error(f"cannot compare {left_type} and {right_type}", node.lineno)
            node.left, node.right = left, right
        return node, DataType.INT

    def check_cast(self, node):
        expr, expr_type = self.check_expr(node.expr)
        if not is_numeric(expr_type):
            self.error(f"cannot cast {expr_type} to {node.target_type}", node.lineno)
        node.expr = expr
        return node, node.target_type

    def check_ternary(self, node):
        cond, cond_type = self.check_expr(node.cond)
        then_e, then_type = self.check_expr(node.then_expr)
        else_e, else_type = self.check_expr(node.else_expr)

        if not is_numeric(cond_type):
            self.error(f"ternary condition must be numeric, got {cond_type}", node.lineno)

        if then_type == else_type:
            result_type = then_type
        elif is_numeric(then_type) and is_numeric(else_type):
            result_type = promote(then_type, else_type)
            then_e = self._maybe_cast(then_e, then_type, result_type, node.lineno)
            else_e = self._maybe_cast(else_e, else_type, result_type, node.lineno)
        else:
            self.error(f"ternary branches have incompatible types: {then_type} and {else_type}",
                       node.lineno)
            result_type = then_type

        node.cond, node.then_expr, node.else_expr = cond, then_e, else_e
        return node, result_type

    def check_assign_stmt(self, stmt):
        entry = self.lookup(stmt.var.name)
        if entry is None:
            self.error(f"undeclared variable '{stmt.var.name}'", stmt.var.lineno)
            expr, expr_type = self.check_expr(stmt.expr)
            stmt.expr = expr
            return stmt

        var_type = entry.getDataType()
        expr, expr_type = self.check_expr(stmt.expr)
        if var_type != expr_type:
            if is_numeric(var_type) and is_numeric(expr_type):
                expr = Cast(var_type, expr, lineno=stmt.lineno)
                expr.result_type = var_type
            else:
                self.error(f"cannot assign {expr_type} to variable '{stmt.var.name}' of type "
                           f"{var_type}", stmt.lineno)
        stmt.expr = expr
        return stmt

    def check_print_stmt(self, stmt):
        expr, expr_type = self.check_expr(stmt.expr)
        stmt.expr = expr
        return stmt

    # ------------------------------------------------------------------
    # WEEK 8 -- control-flow statements
    # ------------------------------------------------------------------
    def check_condition(self, cond, kind, lineno):
        cond, cond_type = self.check_expr(cond)
        if not is_numeric(cond_type):
            self.error(f"{kind} condition must be numeric, got {cond_type}", lineno)
        return cond

    def check_if_stmt(self, stmt):
        stmt.cond = self.check_condition(stmt.cond, "if", stmt.lineno)
        stmt.then_stmt = self.check_stmt(stmt.then_stmt)
        if stmt.else_stmt is not None:
            stmt.else_stmt = self.check_stmt(stmt.else_stmt)
        return stmt

    def check_while_stmt(self, stmt):
        stmt.cond = self.check_condition(stmt.cond, "while", stmt.lineno)
        stmt.body = self.check_stmt(stmt.body)
        return stmt


def check_program(program):
    all_errors = []
    for function in program.getFunctions():
        checker = TypeChecker(program.getGlobalSymbolTable())  # WEEK 8: + globals
        errors = checker.check_function(function)
        all_errors.extend(errors)
    return all_errors
