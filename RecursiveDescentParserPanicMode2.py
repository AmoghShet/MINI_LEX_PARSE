import re
from collections import namedtuple
import subprocess
import os

Token = namedtuple('Token', ['type', 'value', 'line_number', 'column'])

###################################################################################
# LEXER PART
# Define regular expressions for tokens
token_specification = [
    ('BEGIN', r'BEGIN'),                         # Begin keywords
    ('END', r'END'),                             # Begin keywords
    ('PRINT', r'PRINT'),                         # Print keyword
    ('FOR', r'FOR'),                             # For loop
    ('TO', r'TO'),                               # For loop
    ('INTEGER', r'INTEGER'),                     # Integer type
    ('REAL', r'REAL'),                           # Real type
    ('STRING', r'STRING'),                       # String type
    ('ASSIGN', r':='),                           # Assignment operator
    ('COMMA', r','),                             # Comma
    ('ID', r'[A-Za-z][A-Za-z0-9]*'),             # Identifiers
    ('FLOAT', r'[+-]?\d+\.\d+([Ee][+-]?\d+)?'),  # Floating-point numbers
    ('INT', r'[+-]?\d+'),                        # Integer numbers
    ('STRING_LITERAL', r'"[^"]*"'),              # String literals
    ('OPERATOR', r'[+\-*/]\s+'),                 # Operators
    ('WHITESPACE', r'\s+'),                      # Whitespace
]

# Combine the regular expressions into a single pattern
token_pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)
def lexer(input_code):
    line_number = 1
    column = 1

    for match in re.finditer(token_pattern, input_code):
        for name, value in match.groupdict().items():
            if value and name != 'WHITESPACE':
                yield Token(name, value, line_number, column)
                column += len(value)

        line_number += 1
        column = 1
###################################################################################

###################################################################################
# PARSER PART
class Node:
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.children = children if children is not None else []
        self.value = value

    def add_child(self, child):
        self.children.append(child)

    def is_leaf(self):
        return not bool(self.children)

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = None
        self.panic_mode = False  # New flag for panic mode

    def consume(self, expected_type):
        line_number = 1  # Default line number if self.current_token is None

        if self.panic_mode:
            # Get the line number of the current token
            line_number = self.current_token.line_number if self.current_token else 1  # Default to 1 if line number is not available

            # Skip tokens until a synchronization point is found
            while self.current_token and self.current_token.type != expected_type:
                print(f"Skipping: {self.current_token.type}")
                self.current_token = next(self.lexer, None)

            # If synchronization point found, reset panic mode
            if self.current_token and self.current_token.type == expected_type:
                self.panic_mode = False
                self.current_token = next(self.lexer, None)
            else:
                # If synchronization point not found, simply skip the current token and continue
                self.current_token = next(self.lexer, None)
        else:
            if self.current_token and self.current_token.type == expected_type:
                print(f"Consuming: {self.current_token.type}")
                self.current_token = next(self.lexer, None)
            else:
                if self.current_token is None:
                    if expected_type == 'END':
                        # Special case for 'END' at the end of input
                        return
                    raise SyntaxError(f"Unexpected end of input at line {line_number}. Expected '{expected_type}'.")
                else:
                    self.panic_mode = True  # Set panic mode on error
                    print(f"Unexpected token '{self.current_token.type}' at line {self.current_token.line_number}. Expected '{expected_type}'.")
                    # Simply skip the current token and continue
                    self.current_token = next(self.lexer, None)
    
    def program(self):
        program_node = Node('Program')
        self.consume('BEGIN')
        statements_node = self.statement_list()

        if self.current_token:
            while self.current_token and self.current_token.type not in ('END', 'BEGIN'):
                print(f"Skipping: {self.current_token.type}")
                self.current_token = next(self.lexer, None)

        if self.current_token and self.current_token.type == 'BEGIN':
            print("Nested 'BEGIN' found. Error recovery may not be complete.")

        # Consume 'END' if it is present
        if self.current_token and self.current_token.type == 'END':
            self.consume('END')
        else:
            print("Missing 'END'. Error recovery may not be complete.")

        program_node.add_child(statements_node)
        return program_node


    def statement_list(self):
        statements_node = Node('Statements')
        while self.current_token and not self.panic_mode and self.current_token.type in ('PRINT', 'INTEGER', 'REAL', 'STRING', 'ID', 'FOR'):
            statement_node = self.statement()
            statements_node.add_child(statement_node)
        return statements_node

    def statement(self):
        if self.panic_mode:
            # Skip statement parsing until a synchronization point is found
            while self.current_token and self.current_token.type not in ('PRINT', 'INTEGER', 'REAL', 'STRING', 'ID', 'FOR', 'END'):
                self.current_token = next(self.lexer, None)
            return Node('ErrorRecoveryStatement')
        
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
            for_loop_node, start_value, end_value = self.for_loop()
            statement_node = Node(f'START : {start_value}\nEND : {end_value}', [for_loop_node])
        else:
            raise SyntaxError(f"Unexpected token: {self.current_token.type}")

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

        while self.current_token and not self.panic_mode and self.current_token.type == 'ID':
            variable_node = Node('Variable', value=self.current_token.value)
            variable_token = self.current_token  # Save the variable token
            self.consume('ID')
            
            if self.current_token.type == 'ASSIGN':
                # Regular assignment
                self.consume('ASSIGN')
                expression_node = self.expression()
            else:
                # This is the case for FOR loop where no ASSIGN is expected
                expression_node = None

            assignment_node = Node('Assignment', [variable_node, expression_node])
            assignment_node.add_child(Node('Value', [variable_token]))  # Add variable node to Assignment
            assignment_nodes.append(assignment_node)

        return Node('Assignments', assignment_nodes)


    def for_loop(self):
        self.consume('FOR')

        if self.panic_mode:
            # Skip for-loop parsing until a synchronization point is found
            while self.current_token and self.current_token.type not in ('ID', 'END'):
                self.current_token = next(self.lexer, None)
            return Node('ErrorRecoveryForLoop'), None, None

        if self.current_token.type == 'ID':
            start_val_token = self.current_token
            start_val = start_val_token.value
            self.consume('ID')
            self.consume('ASSIGN')
            start_expression = self.expression()
            self.consume('TO')
            end_val_token = self.current_token
            end_value = end_val_token.value
            self.expression()
            statements_node = self.statement_list()  # Get the statements inside the for loop
            self.consume('END')
            return Node('ForLoop', [statements_node]), start_val, end_value
        else:
            # Skip for-loop parsing until a synchronization point is found
            while self.current_token and self.current_token.type not in ('ID', 'END'):
                self.current_token = next(self.lexer, None)
            return Node('ErrorRecoveryForLoop'), None, None

    def expression(self):
        left_term = self.term()
        while self.current_token and not self.panic_mode and self.current_token.type in ('+', '-', '*', '/'):
            operator = self.current_token
            self.consume('OPERATOR')
            
            if self.current_token.type not in {'ID', 'INT', 'FLOAT', 'STRING_LITERAL'}:
                # Skip expression parsing until a synchronization point is found
                self.panic_mode = True
                return Node('ErrorRecoveryExpression')

            right_term = self.term()
            left_term = Token('ID', value=f'{left_term.value} {operator.value} {right_term.value}')
        return left_term
    
    def term(self):
        if self.current_token.type in {'ID', 'INT', 'FLOAT', 'STRING_LITERAL'}:
            cur_token = self.current_token
            self.consume(self.current_token.type)
            return Node('Value', [cur_token])  # Return a Node object instead of Token
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
        max_width = 11
        max_height = 8.5  
        dot_content = [
            'digraph G {',
            'dpi=600;', 
            'rankdir=LR;', 
            f'size="{max_width},{max_height}!";', 
            'ratio="fill";', 
        ]
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
           PRINT "HELLO WORLD"
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
dot_file_path = 'parse_tree.dot'
with open(dot_file_path, 'w') as dot_file:
    dot_file.write(dot_content)

# Generate PNG file
png_file_path = 'parse_tree.png'
subprocess.run(['dot', '-Tpng', dot_file_path, '-o', png_file_path], check=True)

# Open PNG file
try:
    if os.name == 'nt':  # Check if running on Windows
        os.startfile(png_file_path)
    elif os.name == 'posix':  # Check if running on Linux or macOS
        subprocess.run(['xdg-open', png_file_path], check=True)
    else:
        print(f"Unsupported operating system: {os.name}. Please open the file '{png_file_path}' manually.")
except Exception as e:
    print(f"Error opening the PNG file: {e}")