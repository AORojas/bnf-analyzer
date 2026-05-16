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
- Registro, login e historial persistente por usuario con SQLite local o PostgreSQL.

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

## Variables de entorno locales

Para desarrollo local ahora puedes usar un archivo `.env`.

1. Crea una copia de `.env.example`:

```bash
copy .env.example .env
```

2. Edita `.env` con tus valores.

Ejemplo para SQLite local:

```env
SECRET_KEY=dev-bnf-validator-secret
DATABASE_URL=sqlite:///instance/bnf_validator.sqlite3
```

Ejemplo para PostgreSQL local:

```env
SECRET_KEY=dev-bnf-validator-secret
DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/bnf_analyzer
```

La aplicacion carga `.env` automaticamente al iniciar.

## Usuarios e historial persistente

- La aplicacion usa `DATABASE_URL` si esta definida.
- Si no defines `DATABASE_URL`, usa SQLite local en `instance/bnf_validator.sqlite3`.
- Puedes crear una cuenta desde la tarjeta superior derecha.
- Al iniciar sesion, se habilita el guardado de trabajos en base de datos.
- Cada usuario solo ve y administra su propio historial persistente.
- El historial local en `localStorage` sigue disponible como respaldo rapido del navegador.

## PostgreSQL

Para usar PostgreSQL, define una variable de entorno `DATABASE_URL` antes de iniciar la app. Ejemplo:

```bash
set DATABASE_URL=postgresql+psycopg://usuario:clave@localhost:5432/bnf_analyzer
python run.py
```

La app crea las tablas automaticamente al arrancar.

## Migracion de SQLite a PostgreSQL

Si ya tienes datos en `instance/bnf_validator.sqlite3`, puedes copiarlos a PostgreSQL con:

```bash
python scripts/migrate_sqlite_to_postgres.py --sqlite-path instance/bnf_validator.sqlite3 --database-url postgresql+psycopg://usuario:clave@localhost:5432/bnf_analyzer
```

El script:

- crea las tablas destino si no existen
- migra usuarios
- migra historial
- evita duplicar registros si vuelves a ejecutarlo

## Deploy en Render

El proyecto ya incluye un archivo [render.yaml](./render.yaml) para desplegar:

- un `Web Service` Flask con `gunicorn run:app`
- una base `Render Postgres`
- variables `DATABASE_URL` y `SECRET_KEY`

En Render no necesitas `.env`; las variables se toman del `render.yaml` y de los recursos creados por la plataforma.

### Opcion A: deploy automatico con Blueprint

1. Sube el repo a GitHub.
2. En Render entra a `New > Blueprint`.
3. Conecta el repositorio.
4. Render detectara `render.yaml` y te mostrara:
   - `bnf-analyzer` como web service
   - `bnf-analyzer-db` como Postgres
5. Confirma el deploy.

### Opcion B: migrar datos locales antes o despues

Si quieres llevar tus datos actuales a Render:

1. Despliega el proyecto con el `render.yaml`.
2. Copia la `External Database URL` o la `Internal Database URL` desde Render Postgres.
3. Ejecuta localmente:

```bash
python scripts/migrate_sqlite_to_postgres.py --sqlite-path instance/bnf_validator.sqlite3 --database-url "postgresql+psycopg://usuario:clave@host:5432/bnf_analyzer"
```

### Notas de Render

- El `buildCommand` configurado es `pip install -r requirements.txt`.
- El `startCommand` configurado es `gunicorn run:app`.
- Render entrega una `connectionString` de Postgres; la app la normaliza automaticamente para usar `psycopg`.

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
