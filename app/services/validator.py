from __future__ import annotations

from app.services.bnf_parser import Grammar
from app.services.earley import parse_with_earley


EPSILON = "\u03b5"


def validate_strings(
    grammar: Grammar,
    inputs: list[str],
    start_symbol: str,
    derivation_mode: str = "leftmost",
) -> list[dict]:
    results: list[dict] = []
    for raw_value in inputs:
        value = raw_value.rstrip("\r")
        normalized = value.strip()

        if normalized == "":
            continue

        if normalized == EPSILON:
            value = ""

        analysis = parse_with_earley(grammar, value, start_symbol, derivation_mode=derivation_mode)
        results.append(
            {
                "input": EPSILON if value == "" else value,
                "accepted": analysis["accepted"],
                "message": analysis["message"],
                "derivation": analysis["derivation"],
                "derivation_type": analysis.get("derivation_type"),
                "tree": analysis["tree"],
            }
        )
    return results
