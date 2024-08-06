# MINI_LEX_PARSE

Lexer and Parser for a Simple Custom Language

## Overview

This project implements a lexer and a recursive descent parser for a simple custom language. The lexer tokenizes the input code based on predefined regular expressions, and the parser generates a parse tree for the tokenized input, supporting basic constructs such as variable declarations, assignments, and loops. The parser includes error handling with panic mode for recovery from syntax errors.

## Features

- Tokenization of input code into tokens using regular expressions.
- Recursive descent parsing of tokenized input to create a parse tree.
- Support for basic language constructs including `BEGIN`, `END`, `PRINT`, variable declarations (`INTEGER`, `REAL`, `STRING`), assignments, and `FOR` loops.
- Error handling with panic mode for syntax error recovery.
- Generation of a DOT file representing the parse tree and conversion to a PNG image.

## Prerequisites

- Python 3.6 or higher
- Graphviz (for generating the PNG file from the DOT file)

## Installation

1. **Clone the repository:**

    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install Graphviz:**

    - **Ubuntu:**
        ```sh
        sudo apt-get install graphviz
        ```

    - **macOS:**
        ```sh
        brew install graphviz
        ```

    - **Windows:**
        Download and install from [Graphviz](https://graphviz.org/download/).

## Usage

1. **Input Code:**

    The input code is a string containing the program to be tokenized and parsed. Example input:

    ```python
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
         FOR I := 1 TO 5
               PRINT "Strings are [X] and [Y]"
               PRINT "HELLO WORLD"
    END
    """
    ```

2. **Running the Lexer and Parser:**

    ```python
    lexer_instance = lexer(input_code)
    for token in lexer_instance:
        print(token)

    lexer_instance = lexer(input_code)
    parser = Parser(lexer_instance)
    parse_tree = parser.parse()
    dot_content = parser.generate_parse_tree_dot(parse_tree)

    # Save DOT file
    with open('parse_tree.dot', 'w') as dot_file:
        dot_file.write(dot_content)

    # Generate PNG file
    subprocess.run(['dot', '-Tpng', 'parse_tree.dot', '-o', 'parse_tree.png'], check=True)
    ```

3. **Opening the PNG File:**

    ```python
    try:
        if os.name == 'nt':
            os.startfile('parse_tree.png')
        elif os.name == 'posix':
            subprocess.run(['xdg-open', 'parse_tree.png'], check=True)
        else:
            print(f"Unsupported operating system: {os.name}. Please open the file 'parse_tree.png' manually.")
    except Exception as e:
        print(f"Error opening the PNG file: {e}")
    ```

## Explanation

### Lexer

The lexer uses regular expressions to match patterns in the input code and generates tokens. Each token has a type, value, line number, and column.

### Recursive Descent Parser

The parser is implemented as a recursive descent parser, which is a top-down parser built from a set of mutually recursive procedures where each procedure implements one of the non-terminals of the grammar.

#### Parser Methods

- **program()**: Entry point of the parser, parses the entire program.
- **statement_list()**: Parses a list of statements.
- **statement()**: Parses a single statement.
- **var_declaration()**: Parses variable declarations.
- **assignment()**: Parses assignment statements.
- **for_loop()**: Parses `FOR` loop statements.
- **expression()**: Parses expressions.
- **term()**: Parses terms within expressions.

#### Error Handling

The parser includes a panic mode for error recovery. When a syntax error is encountered, the parser enters panic mode, skipping tokens until a synchronization point (such as `NEWLINE` or `END`) is found. This allows the parser to recover and continue parsing the rest of the input.

#### Example

Here's a snippet of how the parser handles variable declarations and assignments:

```python
def var_declaration(self):
    var_type = self.current_token.type
    self.consume(var_type)
    
    var_nodes = [Node(var_type, value=self.current_token.value)]
    self.consume('ID')
    
    while self.current_token.type == 'COMMA':
        self.consume('COMMA')
        var_nodes.append(Node(var_type, value=self.current_token.value))
        self.consume('ID')

    return Node('VarDeclaration', var_nodes)

def assignment(self):
    assignment_nodes = []

    while self.current_token and not self.panic_mode and self.current_token.type == 'ID':
        variable_node = Node('Variable', value=self.current_token.value)
        variable_token = self.current_token
        self.consume('ID')
        
        if self.current_token.type == 'ASSIGN':
            self.consume('ASSIGN')
            expression_node = self.expression()
        else:
            expression_node = None

        assignment_node = Node('Assignment', [variable_node, expression_node])
        assignment_node.add_child(Node('Value', [variable_token]))
        assignment_nodes.append(assignment_node)

    return Node('Assignments', assignment_nodes)
```

### Parse Tree Visualization

The parser generates a DOT file representing the parse tree, which is then converted to a PNG image using Graphviz.

#### Example of DOT Generation

```python
def generate_dot(self, node, dot_content):
    if node is None:
        return

    node_id = id(node)
    label_value = f'{node.type}: {node.value}' if node.value else node.type
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
```

## Files

- `lexer.py`: Contains the lexer implementation.
- `parser.py`: Contains the parser implementation.
- `parse_tree.dot`: Generated DOT file of the parse tree.
- `parse_tree.png`: Generated PNG file of the parse tree.

## License

This project is licensed under the MIT License.
