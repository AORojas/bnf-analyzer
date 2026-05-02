EXAMPLES = [
    {
        "id": "balanced",
        "name": "Parentesis balanceados",
        "description": "Genera secuencias balanceadas de parentesis.",
        "grammar": "<S> ::= ( <S> ) <S> | ε",
        "inputs": "()\n(())\n()()\n(()\n())(",
    },
    {
        "id": "binary",
        "name": "Binarios terminados en 01",
        "description": "Acepta cualquier cadena binaria cuyo sufijo sea 01.",
        "grammar": "<S> ::= <B> 0 1\n<B> ::= 0 <B> | 1 <B> | ε",
        "inputs": "01\n101\n1101\n111\n",
    },
    {
        "id": "expr",
        "name": "Expresiones aritmeticas simples",
        "description": "Expresiones con identificador i, suma y multiplicacion.",
        "grammar": "<expr> ::= <expr> + <term> | <term>\n<term> ::= <term> * <factor> | <factor>\n<factor> ::= ( <expr> ) | i",
        "inputs": "i\ni+i\ni*i\ni+i*i\n(i+i)*i\ni+\n",
    },
]
