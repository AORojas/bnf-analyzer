from __future__ import annotations

from dataclasses import dataclass, field

from app.services.bnf_parser import Grammar, Symbol


EPSILON = "\u03b5"


@dataclass(frozen=True)
class StateKey:
    head: str
    body: tuple[str, ...]
    dot: int
    start: int
    end: int


@dataclass
class ParseNode:
    symbol: str
    children: list["ParseNode"] = field(default_factory=list)
    is_terminal: bool = False

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "is_terminal": self.is_terminal,
            "children": [child.to_dict() for child in self.children],
        }


@dataclass
class State:
    key: StateKey

    @property
    def next_symbol(self) -> str | None:
        if self.key.dot >= len(self.key.body):
            return None
        return self.key.body[self.key.dot]

    @property
    def is_complete(self) -> bool:
        return self.key.dot >= len(self.key.body)


def parse_with_earley(
    grammar: Grammar,
    text: str,
    start_symbol: str,
    derivation_mode: str = "leftmost",
) -> dict:
    tokens = tokenize_input(grammar, text)
    if tokens is None:
        return {
            "accepted": False,
            "tree": None,
            "derivation": [],
            "message": "La cadena contiene fragmentos que no coinciden con ningun terminal de la gramatica.",
        }

    chart: list[dict[StateKey, State]] = [dict() for _ in range(len(tokens) + 1)]
    production_lookup = {
        head: [tuple(symbol.value for symbol in production.body) for production in rules]
        for head, rules in grammar.productions.items()
    }

    for body in production_lookup[start_symbol]:
        key = StateKey(head=start_symbol, body=body, dot=0, start=0, end=0)
        chart[0][key] = State(key=key)

    for index in range(len(chart)):
        changed = True
        while changed:
            changed = False
            for state in list(chart[index].values()):
                if state.is_complete:
                    if _completer(chart, state, index):
                        changed = True
                else:
                    next_symbol = state.next_symbol
                    if next_symbol in grammar.productions:
                        if _predictor(chart, production_lookup, next_symbol, index):
                            changed = True
                    elif index < len(tokens):
                        if _scanner(chart, state, tokens[index], index):
                            changed = True

    completed = [
        state
        for state in chart[len(tokens)].values()
        if state.key.head == start_symbol
        and state.is_complete
        and state.key.start == 0
        and state.key.end == len(tokens)
    ]

    if not completed:
        expected = sorted(
            {
                state.next_symbol
                for state in chart[min(len(tokens), len(chart) - 1)].values()
                if state.next_symbol and state.next_symbol not in grammar.productions
            }
        )
        return {
            "accepted": False,
            "tree": None,
            "derivation": [],
            "message": _build_rejection_message(text, expected),
        }

    tree = build_parse_tree(grammar, tokens, chart, start_symbol)
    if tree is None:
        return {
            "accepted": False,
            "tree": None,
            "derivation": [],
            "message": "La cadena fue reconocida, pero no se pudo reconstruir una derivacion completa.",
        }

    derivation_type = normalize_derivation_mode(derivation_mode)
    derivation = build_derivation(tree, derivation_type)
    if not verify_derivation(tree, grammar, derivation_type):
        return {
            "accepted": False,
            "tree": None,
            "derivation": [],
            "derivation_type": None,
            "message": "La cadena fue reconocida, pero no se pudo construir una derivacion formalmente valida.",
        }

    return {
        "accepted": True,
        "tree": tree.to_dict(),
        "derivation": derivation,
        "derivation_type": derivation_type,
        "message": "La cadena pertenece al lenguaje y fue reconocida completamente.",
    }


def _predictor(chart, production_lookup, symbol, index) -> bool:
    changed = False
    for body in production_lookup[symbol]:
        key = StateKey(head=symbol, body=body, dot=0, start=index, end=index)
        if key not in chart[index]:
            chart[index][key] = State(key=key)
            changed = True
    return changed


def _scanner(chart, state: State, token: str, index: int) -> bool:
    if state.next_symbol != token:
        return False
    key = StateKey(
        head=state.key.head,
        body=state.key.body,
        dot=state.key.dot + 1,
        start=state.key.start,
        end=index + 1,
    )
    if key not in chart[index + 1]:
        chart[index + 1][key] = State(key=key)
        return True
    return False


def _completer(chart, completed_state: State, index: int) -> bool:
    changed = False
    for origin_state in list(chart[completed_state.key.start].values()):
        if origin_state.next_symbol != completed_state.key.head:
            continue
        key = StateKey(
            head=origin_state.key.head,
            body=origin_state.key.body,
            dot=origin_state.key.dot + 1,
            start=origin_state.key.start,
            end=index,
        )
        if key not in chart[index]:
            chart[index][key] = State(key=key)
            changed = True
    return changed


def build_parse_tree(
    grammar: Grammar,
    tokens: list[str],
    chart: list[dict[StateKey, State]],
    start_symbol: str,
) -> ParseNode | None:
    completed_spans = {
        (state.key.head, state.key.start, state.key.end)
        for column in chart
        for state in column.values()
        if state.is_complete
    }
    memo: dict[tuple[str, int, int], ParseNode | None] = {}

    def build_non_terminal(
        symbol: str,
        start: int,
        end: int,
        visiting: set[tuple[str, int, int]],
    ) -> ParseNode | None:
        key = (symbol, start, end)
        if key in memo:
            return memo[key]
        if key in visiting or key not in completed_spans:
            return None

        next_visiting = set(visiting)
        next_visiting.add(key)

        for production in grammar.productions[symbol]:
            children = match_sequence(list(production.body), start, end, next_visiting)
            if children is not None:
                node = ParseNode(symbol=symbol, children=children)
                memo[key] = node
                return node

        memo[key] = None
        return None

    def match_sequence(
        body: list[Symbol],
        start: int,
        end: int,
        visiting: set[tuple[str, int, int]],
    ) -> list[ParseNode] | None:
        if not body:
            return [] if start == end else None

        first, rest = body[0], body[1:]

        if first.is_terminal:
            if start >= end or tokens[start] != first.value:
                return None
            remainder = match_sequence(rest, start + 1, end, visiting)
            if remainder is None:
                return None
            return [ParseNode(symbol=first.value, children=[], is_terminal=True)] + remainder

        for split in range(start, end + 1):
            child = build_non_terminal(first.value, start, split, visiting)
            if child is None:
                continue
            remainder = match_sequence(rest, split, end, visiting)
            if remainder is not None:
                return [child] + remainder

        return None

    return build_non_terminal(start_symbol, 0, len(tokens), set())


def build_derivation(tree: ParseNode, mode: str) -> list[str]:
    normalized_mode = normalize_derivation_mode(mode)
    return build_sentential_derivation(tree, choose_rightmost=normalized_mode == "rightmost")


def normalize_derivation_mode(mode: str) -> str:
    if mode == "rightmost":
        return "rightmost"
    return "leftmost"


def build_sentential_derivation(tree: ParseNode, choose_rightmost: bool) -> list[str]:
    sentential = [tree]
    steps = [_format_sentential_form(sentential)]

    while True:
        candidates = [idx for idx, node in enumerate(sentential) if not node.is_terminal]
        target_index = candidates[-1] if choose_rightmost and candidates else (candidates[0] if candidates else None)
        if target_index is None:
            break
        node = sentential[target_index]
        sentential = sentential[:target_index] + node.children + sentential[target_index + 1 :]
        steps.append(_format_sentential_form(sentential))

    return steps


def verify_derivation(tree: ParseNode, grammar: Grammar, mode: str) -> bool:
    allowed_bodies = {
        head: {tuple(symbol.value for symbol in production.body) for production in productions}
        for head, productions in grammar.productions.items()
    }
    choose_rightmost = normalize_derivation_mode(mode) == "rightmost"
    sentential = [tree]

    while True:
        candidates = [idx for idx, node in enumerate(sentential) if not node.is_terminal]
        target_index = candidates[-1] if choose_rightmost and candidates else (candidates[0] if candidates else None)
        if target_index is None:
            return True

        node = sentential[target_index]
        node_body = tuple(child.symbol for child in node.children)
        if node_body not in allowed_bodies.get(node.symbol, set()):
            return False

        sentential = sentential[:target_index] + node.children + sentential[target_index + 1 :]


def _format_sentential_form(nodes: list[ParseNode]) -> str:
    if not nodes:
        return EPSILON
    rendered = [node.symbol for node in nodes if node.symbol != ""]
    return " ".join(rendered) if rendered else EPSILON


def _build_rejection_message(text: str, expected: list[str]) -> str:
    if text == "":
        if expected:
            return f"La cadena vacia no pudo derivarse. El analizador esperaba uno de: {', '.join(expected)}."
        return "La cadena vacia no pudo derivarse con la gramatica dada."
    if expected:
        return f"La cadena no pertenece al lenguaje. Cerca del final se esperaba uno de: {', '.join(expected)}."
    return "La cadena no pertenece al lenguaje segun la gramatica proporcionada."


def tokenize_input(grammar: Grammar, text: str) -> list[str] | None:
    terminals = sorted(
        {
            symbol.value
            for productions in grammar.productions.values()
            for production in productions
            for symbol in production.body
            if symbol.is_terminal and symbol.value != ""
        },
        key=len,
        reverse=True,
    )

    if not terminals:
        return [] if text.strip() == "" else None

    tokens: list[str] = []
    index = 0
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue

        matched = next((terminal for terminal in terminals if text.startswith(terminal, index)), None)
        if matched is None:
            return None
        tokens.append(matched)
        index += len(matched)

    return tokens
