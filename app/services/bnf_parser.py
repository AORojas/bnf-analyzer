from __future__ import annotations

from dataclasses import dataclass
import re


NON_TERMINAL_PATTERN = re.compile(r"<[^<>\s]+>")
EPSILON_VALUES = {"\u03b5", "epsilon", "EPSILON", "lambda", "LAMBDA"}


@dataclass(frozen=True)
class Symbol:
    value: str
    is_terminal: bool


@dataclass(frozen=True)
class Production:
    head: str
    body: tuple[Symbol, ...]
    raw_body: str
    line: int


@dataclass(frozen=True)
class Grammar:
    productions: dict[str, list[Production]]
    start_symbol: str


class GrammarSyntaxError(ValueError):
    def __init__(self, message: str, line: int | None = None):
        super().__init__(message)
        self.message = message
        self.line = line


def parse_bnf_grammar(grammar_text: str) -> Grammar:
    productions: dict[str, list[Production]] = {}
    first_head: str | None = None

    if not grammar_text.strip():
        raise GrammarSyntaxError("La gramatica esta vacia.")

    for line_number, raw_line in enumerate(grammar_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "::=" not in line:
            raise GrammarSyntaxError(
                "Cada regla debe contener '::=' para separar lado izquierdo y derecho.",
                line_number,
            )

        head_text, body_text = [part.strip() for part in line.split("::=", 1)]
        head = _parse_non_terminal(head_text, line_number, "lado izquierdo")

        if first_head is None:
            first_head = head

        alternatives = [alternative.strip() for alternative in body_text.split("|")]
        if not alternatives:
            raise GrammarSyntaxError(
                "La produccion no tiene alternativas en el lado derecho.",
                line_number,
            )

        parsed_alternatives: list[Production] = []
        for alternative in alternatives:
            symbols = _parse_alternative(alternative, line_number)
            parsed_alternatives.append(
                Production(
                    head=head,
                    body=tuple(symbols),
                    raw_body=alternative,
                    line=line_number,
                )
            )

        productions.setdefault(head, []).extend(parsed_alternatives)

    if not productions or first_head is None:
        raise GrammarSyntaxError("No se encontraron producciones validas.")

    return Grammar(productions=productions, start_symbol=first_head)


def _parse_non_terminal(token: str, line_number: int, context: str) -> str:
    if not NON_TERMINAL_PATTERN.fullmatch(token):
        raise GrammarSyntaxError(
            f"Se esperaba un no terminal valido en el {context}. Usa el formato <simbolo>.",
            line_number,
        )
    return token


def _parse_alternative(alternative: str, line_number: int) -> list[Symbol]:
    if not alternative or alternative in EPSILON_VALUES:
        return []

    symbols: list[Symbol] = []
    for token in _scan_symbols(alternative, line_number):
        if NON_TERMINAL_PATTERN.fullmatch(token):
            symbols.append(Symbol(value=token, is_terminal=False))
        else:
            symbols.append(Symbol(value=_normalize_terminal(token), is_terminal=True))
    return symbols


def _scan_symbols(alternative: str, line_number: int) -> list[str]:
    tokens: list[str] = []
    index = 0

    while index < len(alternative):
        char = alternative[index]

        if char.isspace():
            index += 1
            continue

        if char == "<":
            end_index = alternative.find(">", index + 1)
            if end_index == -1:
                raise GrammarSyntaxError(
                    "Falta '>' de cierre en un no terminal.",
                    line_number,
                )
            token = alternative[index : end_index + 1]
            if not NON_TERMINAL_PATTERN.fullmatch(token):
                raise GrammarSyntaxError(
                    "Se encontro un no terminal invalido. Usa el formato <simbolo>.",
                    line_number,
                )
            tokens.append(token)
            index = end_index + 1
            continue

        if char in {"'", '"'}:
            quote = char
            end_index = index + 1
            while end_index < len(alternative) and alternative[end_index] != quote:
                end_index += 1
            if end_index >= len(alternative):
                raise GrammarSyntaxError(
                    "Hay una comilla sin cerrar en una produccion.",
                    line_number,
                )
            tokens.append(alternative[index : end_index + 1])
            index = end_index + 1
            continue

        end_index = index
        while end_index < len(alternative):
            current = alternative[end_index]
            if current.isspace() or current == "<" or current in {"'", '"'}:
                break
            end_index += 1

        if end_index == index:
            raise GrammarSyntaxError(
                "Hay un token invalido en una produccion. Revisa comillas, espacios o simbolos especiales.",
                line_number,
            )

        tokens.append(alternative[index:end_index])
        index = end_index

    return tokens


def _normalize_terminal(token: str) -> str:
    if len(token) >= 2 and token[0] == token[-1] and token[0] in {"'", '"'}:
        return token[1:-1]
    return token
