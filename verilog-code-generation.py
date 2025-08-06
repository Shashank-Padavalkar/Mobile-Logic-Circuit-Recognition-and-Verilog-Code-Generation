# === Verilog Generator for Final Boolean Expression ===
import re

# Verilog operator map
op_map = {
    'AND': '&',
    'OR': '|',
    'NOT': '~',
    'XOR': '^',
    'XNOR': '~^',
    'NAND': '~&',
    'NOR': '~|',
}

def tokenize(expr):
    expr = expr.upper()
    expr = re.sub(r'([()])', r' \1 ', expr)
    return expr.split()

def infix_to_postfix(tokens):
    precedence = {'NOT': 3, 'AND': 2, 'NAND': 2, 'OR': 1, 'NOR': 1, 'XOR': 1, 'XNOR': 1}
    output, stack = [], []
    for token in tokens:
        if token in op_map:
            while stack and stack[-1] != '(' and precedence.get(stack[-1], 0) >= precedence[token]:
                output.append(stack.pop())
            stack.append(token)
        elif token == '(':
            stack.append(token)
        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack: stack.pop()
        else:
            output.append(token)
    while stack:
        output.append(stack.pop())
    return output

def build_expr_tree(postfix):
    stack = []
    for token in postfix:
        if token in op_map:
            if token == 'NOT':
                operand = stack.pop()
                stack.append((token, operand))
            else:
                right, left = stack.pop(), stack.pop()
                stack.append((token, left, right))
        else:
            stack.append(token)
    return stack[0]

def expr_to_verilog(tree):
    if isinstance(tree, str):
        return tree
    elif tree[0] == 'NOT':
        operand = expr_to_verilog(tree[1])
        return f"(~{operand})"
    else:
        op, left, right = tree
        return f"({expr_to_verilog(left)} {op_map[op]} {expr_to_verilog(right)})"

def generate_verilog_from_expr(boolean_expr, module_name="logic_module"):
    tokens = tokenize(boolean_expr)
    postfix = infix_to_postfix(tokens)
    tree = build_expr_tree(postfix)
    final_expr = expr_to_verilog(tree)

    # Determine all inputs
    inputs = sorted(set(tok for tok in tokens if tok not in op_map and tok not in ("(", ")")))

    verilog = [f"module {module_name}({', '.join(inputs)}, Y);"]
    verilog.append(f"  input {', '.join(inputs)};")
    verilog.append("  output Y;")
    verilog.append(f"  assign Y = {final_expr};")
    verilog.append("endmodule")
    return "\n".join(verilog)

# === Print Verilog HDL Output ===
verilog_code = generate_verilog_from_expr(final_expr)
print("\n===== Generated Verilog HDL =====")
print(verilog_code)
