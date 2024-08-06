import re

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
    ('ID', r'[A-Za-z][A-Za-z0-9_]*'),
    ('FLOAT', r'\d+\.\d+([Ee][-+]?\d+)?'),
    ('INT', r'\d+'),
    ('STRING_LITERAL', r'"[^"]*"'),
    ('WHITESPACE', r'\s+'),
]

token_pattern = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in token_specification)

def lexer(input_code):
    for match in re.finditer(token_pattern, input_code):
        kind, value = next(((name, match.group(name)) for name in match.groupdict() if match.group(name) is not None), (None, None))
        if kind != 'WHITESPACE':
            yield kind, value

class ASTNode:
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class PrintStmt(ASTNode):
    def __init__(self, value):
        self.value = value

class Declaration(ASTNode):
    def __init__(self, var_type, ids):
        self.var_type = var_type
        self.ids = ids

class Assignment(ASTNode):
    def __init__(self, id, value):
        self.id = id
        self.value = value

class ForLoop(ASTNode):
    def __init__(self, id, start, end, body):
        self.id = id
        self.start = start
        self.end = end
        self.body = body

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0

    def look_ahead(self):
        return self.tokens[self.index]

    def consume(self):
        self.index += 1

    def program(self):
        statements = []
        self.consume()  # BEGIN
        while self.look_ahead()[0] != 'END':
            statements.append(self.statement())
        self.consume()  # END
        return Program(statements)

    def statement(self):
        kind, value = self.look_ahead()
        if kind == 'PRINT':
            self.consume()
            _, text = self.look_ahead()
            self.consume()
            return PrintStmt(text)
        elif kind in ['INTEGER', 'REAL', 'STRING']:
            return self.declaration(kind)
        elif kind == 'ID':
            return self.assignment()
        elif kind == 'FOR':
            return self.for_loop()
        else:
            raise Exception(f"Unexpected token {kind}")

    def declaration(self, dtype):
        ids = []
        self.consume()  # dtype
        while True:
            kind, value = self.look_ahead()
            if kind == 'ID':
                ids.append(value)
                self.consume()
            elif kind == 'COMMA':
                self.consume()
            elif kind == 'SEMICOLON':
                self.consume()
                break
        return Declaration(dtype, ids)

    def assignment(self):
        _, var_name = self.look_ahead()
        self.consume()  # var_name
        self.consume()  # :=
        _, value = self.look_ahead()
        self.consume()  # value
        return Assignment(var_name, value)

    def for_loop(self):
        self.consume()  # FOR
        _, loop_var = self.look_ahead()
        self.consume()  # loop_var
        self.consume()  # :=
        _, start = self.look_ahead()
        self.consume()  # start
        self.consume()  # TO
        _, end = self.look_ahead()
        self.consume()  # end
        body = []
        while True:
            kind, _ = self.look_ahead()
            if kind == 'FOR' or kind == 'END':
                break
            body.append(self.statement())
        return ForLoop(loop_var, start, end, body)

def parse(input_code):
    tokens = list(lexer(input_code))
    parser = Parser(tokens)
    return parser.program()


