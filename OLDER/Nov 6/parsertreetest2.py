import re
from collections import namedtuple

###################################################################################
# LEXER PART
# Define regular expressions for tokens
token_specification = [
    ('BEGIN', r'BEGIN'),
    ('END', r'END'),
    ('PRINT', r'PRINT'),
    ('FOR', r'FOR'),
    ('TO', r'TO'),
    ('INTEGER', r'INTEGER'),
    ('REAL', r'REAL'),
    ('STRING', r'STRING'),
    ('ASSIGN', r':='),
    ('COMMA', r','),
    ('SEMICOLON', r';'),
    ('ID', r'[A-Za-z][A-Za-z0-9]*'),  # Identifiers
    ('FLOAT', r'\d+\.\d+'),           # Floating-point numbers
    ('INT', r'\d+'),                  # Integer numbers
    ('STRING_LITERAL', r'"[^"]*"'),   # String literals
    ('OPERATOR', r'[+\-*/]'),         # Operators
    ('WHITESPACE', r'\s+'),           # Whitespace
]

# Combine the regular expressions into a single pattern
token_pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

def lexer(input_code):
    for match in re.finditer(token_pattern, input_code):
        for name, value in match.groupdict().items():
            if value and name != 'WHITESPACE':
                yield Token(name, value)  # Create and yield Token objects
###################################################################################

###################################################################################
# PARSER PART
Token = namedtuple('Token', ['type', 'value'])

class Node:
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.children = children if children is not None else []
        self.value = value

    def add_child(self, child):
        self.children.append(child)

    def is_leaf(self):
        return not bool(self.children)

class Token(namedtuple('Token', ['type', 'value'])):
    def is_leaf(self):
        return True

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None

    def consume(self, expected_type):
        if self.current_token and self.current_token.type == expected_type:
            self.current_token = next(self.lexer, None)
        else:
            if self.current_token is None:
                if expected_type != 'END':
                    raise SyntaxError(f"Unexpected end of input. Expected '{expected_type}'.")
            else:
                raise SyntaxError(f"Unexpected token '{self.current_token.type}'. Expected '{expected_type}'.")

    def program(self):
        program_node = Node('Program')
        self.consume('BEGIN')
        statements_node = self.statement_list()
        self.consume('END')  # Consume the 'END' token
        if self.current_token is not None:
            raise SyntaxError(f"Unexpected tokens found after 'END': {self.current_token.type}")
        program_node.add_child(statements_node)
        return program_node

    def statement_list(self):
        statements_node = Node('Statements')
        while self.current_token and self.current_token.type in ('PRINT', 'INTEGER', 'REAL', 'STRING', 'ID', 'FOR'):
            statement_node = self.statement()
            statements_node.add_child(statement_node)
        return statements_node

    def statement(self):
        if self.current_token.type == 'PRINT':
            self.consume('PRINT')
            string_literal_node = Node('StringLiteral', [Node('Value', [self.current_token])])
            self.consume('STRING_LITERAL')  # Consume the string literal token
            statement_node = Node('PrintStatement', [string_literal_node])
        elif self.current_token.type in ('INTEGER', 'REAL', 'STRING'):
            var_declaration_node = self.var_declaration()
            statement_node = Node('VarDeclaration', [var_declaration_node])
        elif self.current_token.type == 'ID':
            assignment_node = self.assignment()
            statement_node = Node('Assignment', [assignment_node])
        elif self.current_token.type == 'FOR':
            for_loop_node = self.for_loop()
            statement_node = Node('ForLoop', [for_loop_node])
        return statement_node

    def var_declaration(self):
        var_type = self.current_token.type
        self.consume(var_type)
        
        # Create a list to store all variable nodes
        var_nodes = [Node(var_type, value=self.current_token.value)]
        
        self.consume('ID')
        
        while self.current_token.type == 'COMMA':
            self.consume('COMMA')
            var_nodes.append(Node(var_type, value=self.current_token.value))
            self.consume('ID')

        return Node('VarDeclaration', var_nodes)

    def assignment(self):
        assignment_nodes = []  # Create a list to store all assignment nodes

        while self.current_token and self.current_token.type == 'ID':
            variable_node = Node('Variable', value=self.current_token.value)
            variable_token = self.current_token  # Save the variable token
            self.consume('ID')
            self.consume('ASSIGN')
            expression_node = self.expression()
            assignment_node = Node('Assignment', [variable_node, expression_node])
            assignment_node.add_child(Node('Variable', [Node('Value', [variable_token])]))  # Add variable node to Assignment
            assignment_nodes.append(assignment_node)

        return Node('Assignments', assignment_nodes)

    def for_loop(self):
        self.consume('FOR')
        self.consume('ID')
        self.consume('ASSIGN')
        self.expression()
        self.consume('TO')
        self.expression()
        statements_node = self.statement_list()  # Get the statements inside the for loop
        self.consume('END')
        return Node('ForLoop', [statements_node])

    def expression(self):
        left_term = self.term()
        while self.current_token.type in ('+', '-', '*', '/'):
            operator = self.current_token
            self.consume('OPERATOR')
            right_term = self.term()
            left_term_node = Node('ID', value=f'({left_term.value})') if left_term.type == 'ID' else Node(left_term.type, value=left_term.value)
            right_term_node = Node('ID', value=f'({right_term.value})') if right_term.type == 'ID' else Node(right_term.type, value=right_term.value)
            left_term = Token('ID', value=f'{left_term_node.value} {operator.value} {right_term_node.value}')

        self.current_token = left_term  # Update self.current_token with a new Token object
        return left_term

    def term(self):
        if self.current_token.type == 'ID':
            self.consume('ID')
        elif self.current_token.type == 'INT':
            self.consume('INT')
        elif self.current_token.type == 'FLOAT':
            self.consume('FLOAT')
        elif self.current_token.type == 'STRING_LITERAL':
            self.consume('STRING_LITERAL')
        else:
            raise SyntaxError(f"Unexpected token: {self.current_token.type}")
        
    def generate_dot(self, node, dot_content):
        if node is None:
            return

        node_id = id(node)
        label_value = f'{node.type}: {node.value}' if node.value else node.type
        # Escape double quotes in the label
        label_value = label_value.replace('"', r'\"')
        label = f'label="{label_value}"'
        dot_content.append(f'{node_id} [{label}]')

        if isinstance(node, Node) and not node.is_leaf():
            for child in node.children:
                child_id = id(child)
                dot_content.append(f'{node_id} -> {child_id}')
                self.generate_dot(child, dot_content)

    def generate_parse_tree_dot(self, parse_tree):
        dot_content = ['digraph G {']
        self.generate_dot(parse_tree, dot_content)
        dot_content.append('}')
        return '\n'.join(dot_content)

    def parse(self):
        self.current_token = next(self.lexer)
        program_node = self.program()
        return program_node
###################################################################################

###################################################################################
# DRIVER CODE 
input_code = """
BEGIN
     PRINT "HELLO"
     INTEGER A, B, C
     REAL D, E
     STRING X, Y
     A := 2
     B := 4
     C := 6
     D := -3.56E-8
     E := 4.567
     X := "text1"
     Y := "hello there"
     FOR I:= 1 TO 5
           PRINT "Strings are [X] and [Y]"
END
"""

lexer_instance = lexer(input_code)
for token in lexer_instance:
    print(token)

# Create a new lexer instance for parsing 
lexer_instance = lexer(input_code)
parser = Parser(lexer_instance)
parse_tree = parser.parse()

# Generate DOT content
dot_content = parser.generate_parse_tree_dot(parse_tree)

# Save DOT file
with open('parse_tree.dot', 'w') as dot_file:
    dot_file.write(dot_content)