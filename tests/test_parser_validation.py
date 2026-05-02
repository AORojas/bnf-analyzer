from app.services.bnf_parser import parse_bnf_grammar
from app.services.validator import validate_strings


ASSIGNMENT_GRAMMAR = """
<asig> ::= <id> := <exp>
<id> ::= <letra> | <id><letra> | <id><digito>
<exp> ::= <exp> + <termino> | <exp> - <termino> | <termino>
<termino> ::= <termino> * <id> | <termino> / <id> | <id>
<letra> ::= a | b | c | x | y | z
<digito> ::= 0 | 1 | 2 | 9
""".strip()


def test_assignment_grammar_accepts_valid_identifiers_and_expressions():
    grammar = parse_bnf_grammar(ASSIGNMENT_GRAMMAR)

    results = validate_strings(grammar, ["ab := c1", "ab := x9+y2"], "<asig>", "leftmost")

    assert [result["accepted"] for result in results] == [True, True]
    assert results[0]["derivation"][-1] == "a b := c 1"
    assert results[1]["derivation"][-1] == "a b := x 9 + y 2"


def test_assignment_grammar_rejects_numeric_expression_without_identifier():
    grammar = parse_bnf_grammar(ASSIGNMENT_GRAMMAR)

    results = validate_strings(grammar, ["ab := 11", "ab := 1+x"], "<asig>", "leftmost")

    assert [result["accepted"] for result in results] == [False, False]
    assert all(result["derivation"] == [] for result in results)
