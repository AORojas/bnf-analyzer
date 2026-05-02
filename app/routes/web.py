from flask import Blueprint, g, jsonify, render_template, request, session

from app.persistence import (
    authenticate_user,
    create_history_entry,
    create_user,
    delete_history_entry,
    get_user_by_username,
    list_history_entries,
)
from app.services.bnf_parser import GrammarSyntaxError, parse_bnf_grammar
from app.services.examples import EXAMPLES
from app.services.validator import validate_strings

web_bp = Blueprint("web", __name__)


@web_bp.get("/")
def index():
    return render_template("index.html", examples=EXAMPLES, current_user=g.user)


@web_bp.get("/biblioteca")
def library():
    entries = list_history_entries(g.user["id"]) if g.user else []
    return render_template("library.html", current_user=g.user, entries=entries)


@web_bp.get("/api/examples")
def get_examples():
    return jsonify({"examples": EXAMPLES})


@web_bp.post("/api/validate")
def validate():
    payload = request.get_json(silent=True) or {}
    grammar_text = payload.get("grammar", "")
    raw_inputs = payload.get("inputs", "")
    selected_start_symbol = payload.get("start_symbol")
    derivation_mode = payload.get("derivation_mode", "leftmost")

    try:
        grammar = parse_bnf_grammar(grammar_text)
    except GrammarSyntaxError as exc:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "type": "grammar_syntax",
                        "message": exc.message,
                        "line": exc.line,
                    }
                }
            ),
            400,
        )

    start_symbol = selected_start_symbol or grammar.start_symbol
    if start_symbol not in grammar.productions:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "type": "invalid_start_symbol",
                        "message": f"El simbolo inicial {start_symbol} no existe en la gramatica.",
                    }
                }
            ),
            400,
        )

    inputs = raw_inputs.splitlines()
    results = validate_strings(grammar, inputs, start_symbol, derivation_mode=derivation_mode)
    return jsonify(
        {
            "ok": True,
            "start_symbol": start_symbol,
            "derivation_mode": derivation_mode,
            "available_start_symbols": sorted(grammar.productions.keys()),
            "results": results,
        }
    )


@web_bp.get("/api/auth/me")
def get_current_user():
    return jsonify({"ok": True, "user": g.user})


@web_bp.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip().lower()
    password = payload.get("password") or ""

    if len(username) < 3:
        return jsonify({"ok": False, "error": {"message": "El usuario debe tener al menos 3 caracteres."}}), 400
    if len(password) < 6:
        return jsonify({"ok": False, "error": {"message": "La contrasena debe tener al menos 6 caracteres."}}), 400
    if get_user_by_username(username):
        return jsonify({"ok": False, "error": {"message": "Ese usuario ya existe."}}), 400

    user = create_user(username, password)
    session["user_id"] = user["id"]
    return jsonify({"ok": True, "user": user})


@web_bp.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = payload.get("username") or ""
    password = payload.get("password") or ""
    user = authenticate_user(username, password)
    if user is None:
        return jsonify({"ok": False, "error": {"message": "Usuario o contrasena incorrectos."}}), 401

    session["user_id"] = user["id"]
    return jsonify({"ok": True, "user": user})


@web_bp.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@web_bp.get("/api/history")
def get_history():
    if g.user is None:
        return jsonify({"ok": False, "error": {"message": "Debes iniciar sesion para ver tu historial guardado."}}), 401
    return jsonify({"ok": True, "entries": list_history_entries(g.user["id"])})


@web_bp.post("/api/history")
def save_history():
    if g.user is None:
        return jsonify({"ok": False, "error": {"message": "Debes iniciar sesion para guardar tus trabajos."}}), 401

    payload = request.get_json(silent=True) or {}
    grammar = payload.get("grammar", "").strip()
    inputs = payload.get("inputs", "")
    label = (payload.get("label") or "Trabajo guardado").strip()
    start_symbol = payload.get("start_symbol")
    derivation_mode = payload.get("derivation_mode", "leftmost")

    if not grammar:
        return jsonify({"ok": False, "error": {"message": "No puedes guardar un trabajo sin gramatica."}}), 400

    entry = create_history_entry(
        user_id=g.user["id"],
        label=label[:120],
        grammar=grammar,
        inputs=inputs,
        start_symbol=start_symbol,
        derivation_mode=derivation_mode,
    )
    return jsonify({"ok": True, "entry": entry})


@web_bp.delete("/api/history/<int:entry_id>")
def remove_history(entry_id: int):
    if g.user is None:
        return jsonify({"ok": False, "error": {"message": "Debes iniciar sesion para modificar tu historial."}}), 401
    deleted = delete_history_entry(g.user["id"], entry_id)
    if not deleted:
        return jsonify({"ok": False, "error": {"message": "No se encontro la entrada solicitada."}}), 404
    return jsonify({"ok": True})
