import ast
import astpretty


code = """
def foo(x):
    return x + 1
"""

tree = ast.parse(code)
print(ast.dump(tree))
#astpretty.pprint(ast.parse(code))
