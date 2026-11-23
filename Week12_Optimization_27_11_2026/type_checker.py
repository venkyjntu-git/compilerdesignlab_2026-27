"""
TinyCStr Levels 1-4 -- Semantic Analysis / Type Checker.

REFERENCE IMPLEMENTATION, fully complete through Level 4.

History: Week 6 wrote the expression rules; Week 7 stamps
`node.result_type` on every expression; Week 8 added globals and
if/while/block.

WEEK 10 -- functions. Checking now happens in three passes:

  1. build_function_table(): whole-program rules about function
     DECLARATIONS -- duplicate definitions, unnamed or duplicate
     parameters, a local redeclaring a parameter, and prototypes that
     don't match (or never get) a definition. Produces the function table
     (name -> FunctionSignature) that pass 3 uses to check calls.
  2. check_main(): exactly one main, declared as `int main()`.
  3. A TypeChecker per function body. Names resolve locals -> parameters
     -> globals; calls are checked against the function table
     (check_call), returns against the enclosing function (check_return).

Arguments and return values get the same implicit numeric conversion
an assignment already gets: an int passed to a double parameter is
wrapped in an inserted Cast(DOUBLE), visible in `-check` output.

Warnings never stop compilation. There is one: a named parameter that
the body never uses -- usually a sign of a typo such as using a global
instead of the parameter (Slide 7's Example 4 has exactly this bug).
"""
from ast_nodes import (Const, Var, Assign, Print, BinOp, RelOp, Cast, Ternary, If, While,
                       Block, FunctionCall, Return)
from SymbolTable import DataType
from type_rules import is_numeric, promote, SemanticError


class FunctionSignature:
    """What a caller needs to know about a function: return type and parameter types."""

    def __init__(self, name, return_type, param_types, lineno=None):
        self.name = name
        self.return_type = return_type
        self.param_types = list(param_types)
        self.lineno = lineno


# ----------------------------------------------------------------------
# Pass 1 -- function declarations
# ----------------------------------------------------------------------
def build_function_table(program, errors):
    table = {}
    for func in program.getFunctions():
        name = func.getName()
        if name in table:
            errors.append(SemanticError(f"function '{name}' defined more than once",
                                        func.getLineno()))
            continue
        table[name] = FunctionSignature(name, func.getReturnType(), func.getParamTypes(),
                                        func.getLineno())
        seen = set()
        for i, (_, pname) in enumerate(func.getParamList(), start=1):
            if pname is None:
                errors.append(SemanticError(f"parameter {i} of '{name}' has no name",
                                            func.getLineno()))
            elif pname in seen:
                errors.append(SemanticError(f"duplicate parameter '{pname}' in '{name}'",
                                            func.getLineno()))
            else:
                seen.add(pname)
        for entry in func.getLocalSymbolTable().table:
            if entry.getSymbolName() in seen:
                errors.append(SemanticError(
                    f"local variable '{entry.getSymbolName()}' in '{name}' redeclares a parameter",
                    func.getLineno()))

    for proto in program.getPrototypes():
        sig = table.get(proto.getName())
        if sig is None:
            errors.append(SemanticError(
                f"function '{proto.getName()}' declared but never defined", proto.getLineno()))
            # still callable as far as type checking goes -- avoids a second,
            # misleading "undefined function" error at every call site
            table[proto.getName()] = FunctionSignature(
                proto.getName(), proto.getReturnType(), proto.getParamTypes(), proto.getLineno())
        elif (sig.return_type != proto.getReturnType()
              or sig.param_types != proto.getParamTypes()):
            errors.append(SemanticError(
                f"prototype of '{proto.getName()}' does not match its definition",
                proto.getLineno()))
    return table


# ----------------------------------------------------------------------
# Pass 2 -- main
# ----------------------------------------------------------------------
def check_main(program, table, errors):
    sig = table.get('main')
    if sig is None:
        errors.append(SemanticError("program has no 'main' function", None))
    elif sig.return_type != DataType.INT or sig.param_types:
        errors.append(SemanticError("'main' must be declared as int main() with no parameters",
                                    sig.lineno))


# ----------------------------------------------------------------------
# Pass 3 -- function bodies
# ----------------------------------------------------------------------
class TypeChecker:
    def __init__(self, global_symbol_table=None, function_table=None):
        self.errors = []
        self.warnings = []
        self.global_symbol_table = global_symbol_table
        self.function_table = function_table if function_table is not None else {}
        self.function = None
        self.param_symbol_table = None
        self.used_params = set()

    def lookup(self, name):
        """WEEK 10: locals, then parameters, then globals; None if in none of them."""
        entry = self.symbol_table.getSymbol(name)
        if entry is None and self.param_symbol_table is not None:
            entry = self.param_symbol_table.getSymbol(name)
            if entry is not None:
                self.used_params.add(name)
        if entry is None and self.global_symbol_table is not None:
            entry = self.global_symbol_table.getSymbol(name)
        return entry

    def error(self, message, lineno):
        self.errors.append(SemanticError(message, lineno))

    def check_function(self, function):
        self.function = function
        self.symbol_table = function.getLocalSymbolTable()
        self.param_symbol_table = function.getParamSymbolTable()
        self.used_params = set()
        checked_stmts = []
        for stmt in function.getStatementsAstList():
            checked_stmts.append(self.check_stmt(stmt))
        function.setStatementsAstList(checked_stmts)
        for entry in self.param_symbol_table.table:
            if entry.getSymbolName() not in self.used_params:
                self.warnings.append(SemanticError(
                    f"parameter '{entry.getSymbolName()}' of '{function.getName()}' is never used",
                    function.getLineno()))
        return self.errors

    def check_stmt(self, stmt):
        if isinstance(stmt, Assign):
            return self.check_assign_stmt(stmt)
        elif isinstance(stmt, Print):
            return self.check_print_stmt(stmt)
        elif isinstance(stmt, If):
            return self.check_if_stmt(stmt)
        elif isinstance(stmt, While):
            return self.check_while_stmt(stmt)
        elif isinstance(stmt, Block):
            stmt.stmts = [self.check_stmt(s) for s in stmt.stmts]
            return stmt
        elif isinstance(stmt, FunctionCall):    # WEEK 10: a call used as a statement
            node, _ = self.check_call(stmt, as_statement=True)
            return node
        elif isinstance(stmt, Return):          # WEEK 10
            return self.check_return(stmt)
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
        elif isinstance(node, FunctionCall):    # WEEK 10
            result_node, result_type = self.check_call(node)
        else:
            raise ValueError(f"unexpected expr node type: {type(node)}")
        result_node.result_type = result_type
        return result_node, result_type

    def _maybe_cast(self, child, child_type, target_type, lineno):
        if child_type != target_type:
            cast = Cast(target_type, child, lineno=lineno)
            cast.result_type = target_type
            return cast
        return child

    # ------------------------------------------------------------------
    # WEEK 10 -- calls and returns
    # ------------------------------------------------------------------
    def check_call(self, node, as_statement=False):
        checked = [self.check_expr(arg) for arg in node.args]
        node.args = [arg for arg, _ in checked]
        sig = self.function_table.get(node.name)
        if sig is None:
            self.error(f"call to undefined function '{node.name}'", node.lineno)
            return node, DataType.INT
        # WEEK 11: the callee's DECLARED return type, for code generation -- even
        # for a statement call, which is never stamped with a result_type
        node.return_type = sig.return_type
        if len(checked) != len(sig.param_types):
            self.error(f"function '{node.name}' expects {len(sig.param_types)} argument(s), "
                       f"got {len(checked)}", node.lineno)
        else:
            new_args = []
            for i, ((arg, arg_type), param_type) in enumerate(zip(checked, sig.param_types),
                                                              start=1):
                if arg_type != param_type:
                    if is_numeric(arg_type) and is_numeric(param_type):
                        arg = self._maybe_cast(arg, arg_type, param_type, node.lineno)
                    else:
                        self.error(f"argument {i} of '{node.name}': cannot pass {arg_type} "
                                   f"as {param_type}", node.lineno)
                new_args.append(arg)
            node.args = new_args
        if sig.return_type == DataType.VOID and not as_statement:
            self.error(f"void function '{node.name}' used in an expression", node.lineno)
            return node, DataType.INT   # avoid a second, cascading error in the caller
        return node, sig.return_type

    def check_return(self, stmt):
        rtype = self.function.getReturnType()
        fname = self.function.getName()
        if stmt.expr is None:
            if rtype != DataType.VOID:
                self.error(f"return without a value in function '{fname}' returning {rtype}",
                           stmt.lineno)
            return stmt
        expr, expr_type = self.check_expr(stmt.expr)
        if rtype == DataType.VOID:
            self.error(f"return with a value in void function '{fname}'", stmt.lineno)
        elif expr_type != rtype:
            if is_numeric(expr_type) and is_numeric(rtype):
                expr = self._maybe_cast(expr, expr_type, rtype, stmt.lineno)
            else:
                self.error(f"cannot return {expr_type} from function '{fname}' returning {rtype}",
                           stmt.lineno)
        stmt.expr = expr
        return stmt

    # ------------------------------------------------------------------
    # Levels 1-3 -- unchanged
    # ------------------------------------------------------------------
    def check_var(self, node):
        entry = self.lookup(node.name)
        if entry is None:
            self.error(f"undeclared variable '{node.name}'", node.lineno)
            return node, DataType.INT
        return node, entry.getDataType()

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


def check_program(program, warnings=None):
    """
    Returns the list of errors (empty = OK). If a `warnings` list is passed,
    warnings are appended to it -- they never count as errors.
    """
    all_errors = []
    table = build_function_table(program, all_errors)
    check_main(program, table, all_errors)
    for function in program.getFunctions():
        checker = TypeChecker(program.getGlobalSymbolTable(), table)
        all_errors.extend(checker.check_function(function))
        if warnings is not None:
            warnings.extend(checker.warnings)
    # report in SOURCE order (whole-program errors, which have no line, first) --
    # the passes above find them in a different order. sort() is stable.
    by_line = lambda e: (e.lineno is not None, e.lineno or 0)
    all_errors.sort(key=by_line)
    if warnings is not None:
        warnings.sort(key=by_line)
    return all_errors
