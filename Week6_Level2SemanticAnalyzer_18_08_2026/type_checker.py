from ast_nodes import (
    Const,
    Var,
    Assign,
    Print,
    BinOp,
    RelOp,
    Cast,
    Ternary
)

from SymbolTable import DataType
from type_rules import is_numeric, promote, SemanticError


class TypeChecker:

    def __init__(self, function):
        self.function = function
        self.symbol_table = function.getLocalSymbolTable()
        self.errors = []

    def error(self, message, lineno):
        self.errors.append(
            SemanticError(message, lineno)
        )

    def check_var(self, node):
        if not self.symbol_table.nameInSymbolTable(node.name):
            self.error(
                f"undeclared variable '{node.name}'",
                node.lineno
            )
            return node, DataType.INT

        symbol = self.symbol_table.getSymbol(node.name)

        return node, symbol.getDataType()

    def check_expr(self, node):

        if isinstance(node, Const):
            return node, node.type

        if isinstance(node, Var):
            return self.check_var(node)

        if isinstance(node, BinOp):
            return self.check_binop(node)

        if isinstance(node, RelOp):
            return self.check_relop(node)

        if isinstance(node, Cast):
            return self.check_cast(node)

        if isinstance(node, Ternary):
            return self.check_ternary(node)

        return node, DataType.INT

    def check_binop(self, node):

        new_left, left_type = self.check_expr(node.left)
        new_right, right_type = self.check_expr(node.right)

        node.left = new_left
        node.right = new_right

        if not is_numeric(left_type) or not is_numeric(right_type):
            self.error(
                f"invalid operands to '{node.op}'",
                node.lineno
            )
            return node, DataType.INT

        result_type = promote(left_type, right_type)

        if left_type != result_type:
            node.left = Cast(
                result_type,
                node.left,
                node.left.lineno
            )

        if right_type != result_type:
            node.right = Cast(
                result_type,
                node.right,
                node.right.lineno
            )

        return node, result_type

    def check_relop(self, node):

        new_left, left_type = self.check_expr(node.left)
        new_right, right_type = self.check_expr(node.right)

        node.left = new_left
        node.right = new_right

        if not is_numeric(left_type) or not is_numeric(right_type):
            self.error(
                f"invalid operands to '{node.op}'",
                node.lineno
            )
            return node, DataType.INT

        common_type = promote(left_type, right_type)

        if left_type != common_type:
            node.left = Cast(
                common_type,
                node.left,
                node.left.lineno
            )

        if right_type != common_type:
            node.right = Cast(
                common_type,
                node.right,
                node.right.lineno
            )

        return node, DataType.INT

    def check_ternary(self, node):

        new_cond, cond_type = self.check_expr(node.cond)
        new_then, then_type = self.check_expr(node.then_expr)
        new_else, else_type = self.check_expr(node.else_expr)

        node.cond = new_cond
        node.then_expr = new_then
        node.else_expr = new_else

        if not is_numeric(cond_type):
            self.error(
                "ternary condition must be numeric",
                node.cond.lineno
            )

        if then_type == else_type:
            return node, then_type

        if is_numeric(then_type) and is_numeric(else_type):

            common_type = promote(
                then_type,
                else_type
            )

            if then_type != common_type:
                node.then_expr = Cast(
                    common_type,
                    node.then_expr,
                    node.then_expr.lineno
                )

            if else_type != common_type:
                node.else_expr = Cast(
                    common_type,
                    node.else_expr,
                    node.else_expr.lineno
                )

            return node, common_type

        self.error(
            "incompatible types in ternary expression",
            node.lineno
        )

        return node, DataType.INT

    def check_cast(self, node):

        new_expr, expr_type = self.check_expr(node.expr)

        node.expr = new_expr

        target_type = node.target_type

        if is_numeric(expr_type) and is_numeric(target_type):
            return node, target_type

        if expr_type == target_type:
            return node, target_type

        self.error(
            f"invalid cast from {expr_type.name} to {target_type.name}",
            node.lineno
        )

        return node, target_type

    def check_assign_stmt(self, node):

        new_var, var_type = self.check_var(node.var)
        node.var = new_var

        new_expr, expr_type = self.check_expr(node.expr)
        node.expr = new_expr

        if var_type == expr_type:
            return node

        if is_numeric(var_type) and is_numeric(expr_type):
            node.expr = Cast(
                var_type,
                node.expr,
                node.expr.lineno
            )
            return node

        self.error(
            f"cannot assign {expr_type.name} to {var_type.name}",
            node.lineno
        )

        return node

    def check_stmt(self, node):

        if isinstance(node, Assign):
            return self.check_assign_stmt(node)

        if isinstance(node, Print):
            new_expr, expr_type = self.check_expr(node.expr)
            node.expr = new_expr
            return node

        return node

    def check_function(self):

        statements = self.function.getStatementsAstList()

        for i in range(len(statements)):
            statements[i] = self.check_stmt(statements[i])

        return self.errors


def check_program(program):

    all_errors = []

    for function in program.getFunctions():

        checker = TypeChecker(function)

        errors = checker.check_function()

        all_errors.extend(errors)

    return all_errors

