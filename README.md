# Validador Web de Gramaticas BNF

Aplicacion web educativa construida con Flask para validar cadenas contra gramaticas escritas en BNF.

## Caracteristicas

- Editor de gramatica BNF con validacion sintactica.
- Soporte para recursion izquierda y multiples no terminales mediante parser Earley.
- Validacion de multiples cadenas, una por linea.
- Seleccion de simbolo inicial.
- Selector del tipo de derivacion mostrada: izquierda o derecha.
- Derivacion paso a paso para cadenas aceptadas, con izquierda como opcion recomendada por claridad.
- Arbol de parsing textual.
- Ejemplos precargados para practicar.
- Autoguardado local e historial de versiones en el navegador.
- Registro, login e historial persistente por usuario en SQLite.

## Estructura

```text
app/
  routes/        # Rutas web y API JSON
  services/      # Parser BNF, algoritmo Earley, validacion y ejemplos
  static/        # CSS y JavaScript
  templates/     # Plantillas HTML
run.py           # Punto de entrada
requirements.txt
```

## Requisitos

- Python 3.11 o superior

## Ejecucion local

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Luego abre `http://127.0.0.1:5000`.

## Usuarios e historial persistente

- La aplicacion crea automaticamente una base SQLite en `instance/bnf_validator.sqlite3`.
- Puedes crear una cuenta desde la tarjeta superior derecha.
- Al iniciar sesion, se habilita el guardado de trabajos en base de datos.
- Cada usuario solo ve y administra su propio historial persistente.
- El historial local en `localStorage` sigue disponible como respaldo rapido del navegador.

## Formato BNF soportado

```bnf
<expr> ::= <expr> + <term> | <term>
<term> ::= <term> * <factor> | <factor>
<factor> ::= ( <expr> ) | i
```

Reglas admitidas:

- No terminales en formato `<simbolo>`.
- Alternativas con `|`.
- Terminales simples como `+`, `(`, `i`, `0`.
- Terminales entre comillas, por ejemplo `"if"` o `'while'`.
- Producciones vacias usando `ε`, `epsilon`, `lambda` o dejando la alternativa vacia.

## Notas de uso

- El analizador consume la cadena completa; no acepta coincidencias parciales.
- El motor tokeniza la cadena de entrada caracter por caracter, por lo que los terminales del ejemplo deben reflejar exactamente los simbolos esperados.
- Si quieres validar tokens de varias letras sin espacios, definalos entre comillas en la gramatica, por ejemplo `"if"`.
- Las lineas vacias en el bloque de entradas se ignoran. Si quieres validar la cadena vacia, escribe `ε` como entrada.
- El historial y el autoguardado se almacenan en `localStorage`, por lo que quedan asociados al navegador y equipo donde trabajes.
