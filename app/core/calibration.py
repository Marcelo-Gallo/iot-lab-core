import ast
import operator
import math

# Operadores permitidos (Whitelist)
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Funções permitidas
FUNCTIONS = {
    "sqrt": math.sqrt,
    "log": math.log,
    "abs": abs,
    "round": round
}

def safe_eval(formula: str, x_value: float) -> float:
    """
    Avalia uma expressão matemática contendo 'x' de forma segura.
    Não usa eval() nativo. Usa AST Parsing com whitelist.
    
    Ex: safe_eval("x * 0.5 + 10", 100) -> 60.0
    """
    if not formula or not formula.strip():
        return x_value

    try:
        # Limita o tamanho para evitar Denial of Service por memória
        if len(formula) > 50:
            raise ValueError("Fórmula muito longa")

        # Parseia a string para uma árvore sintática abstrata (AST)
        node = ast.parse(formula, mode='eval')
        
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Name):
                if node.id == 'x':
                    return x_value
                raise ValueError(f"Variável não permitida: {node.id}")
            elif isinstance(node, ast.BinOp):
                op = type(node.op)
                if op in OPERATORS:
                    return OPERATORS[op](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp):
                op = type(node.op)
                if op in OPERATORS:
                    return OPERATORS[op](_eval(node.operand))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
                    args = [_eval(arg) for arg in node.args]
                    return FUNCTIONS[node.func.id](*args)
            
            raise ValueError(f"Expressão inválida ou insegura: {type(node)}")

        return float(_eval(node))

    except Exception as e:
        print(f"Erro de Calibração (Fórmula: '{formula}'): {e}")
        return x_value