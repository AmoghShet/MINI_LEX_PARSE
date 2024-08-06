import re

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
                yield name, value

# Example usage
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

for token in lexer(input_code):
    print(token)
