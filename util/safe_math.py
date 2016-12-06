"""Utility functions to safely evaluate mathematical expressions."""
import ast
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.BitXor: op.xor,
             ast.USub: op.neg} # ast.Pow: op.pow

def eval_expr(expr):
    """Parse a mathematical expression for eval_()."""
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    """Calculate a mathematical expression."""
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

def power(a, b):
    if any(abs(n) > 900 for n in [a, b]):
        raise ValueError((a,b))
    return op.pow(a, b)
operators[ast.Pow] = power
