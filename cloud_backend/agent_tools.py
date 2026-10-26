"""A fast, deterministic, bounded calculator tool for HOSHI.

OpenJarvis-inspired tool routing: direct safe calculations don't consume
LLM tokens or pretend that a model calculated an answer.
"""
import ast
import math
import operator
import re


_ALLOWED_BINARY = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                   ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_ALLOWED_UNARY = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_PREFIX = re.compile(r"^\s*(?:what(?:'s| is)?|calculate|calc|solve|hisab|hisaab|kitna(?: hota hai)?|"
                     r"what is|count)\s*[:：]?\s*", re.I)
_EXPR = re.compile(r"\A[0-9.\s+\-*/()%^×÷]+\Z")


def _eval(node, depth=0):
    if depth > 12:
        raise ValueError("Expression is too complicated.")
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        value = float(node.value)
    elif isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINARY:
        a = _eval(node.left, depth+1)
        b = _eval(node.right, depth+1)
        if isinstance(node.op, ast.Pow) and (abs(b) > 8 or abs(a) > 1e5):
            raise ValueError("Exponent is too large.")
        value = _ALLOWED_BINARY[type(node.op)](a, b)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARY:
        value = _ALLOWED_UNARY[type(node.op)](_eval(node.operand, depth+1))
    else:
        raise ValueError("Unsupported calculator expression.")
    if not math.isfinite(value) or abs(value)>1e12:
        raise ValueError("Result exceeds calculator limit.")
    return value


def try_calculate(message):
    text = str(message or "").strip()
    candidate = _PREFIX.sub("", text).rstrip(" ?۔؟").strip()
    candidate = candidate.replace("×", "*").replace("÷", "/").replace("^", "**")
    if not candidate or len(candidate) > 100 or not _EXPR.fullmatch(candidate):
        return None
    # Require an operator; plain numerical messages shouldn't trigger.
    if not re.search(r"[+*/%\-]", candidate[1:]) and not candidate.startswith(("-", "+")):
        return None
    try:
        parsed=ast.parse(candidate,mode="eval")
        answer=_eval(parsed.body)
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError):
        return None
    result = int(answer) if answer.is_integer() else round(answer, 8)
    return str(result)
