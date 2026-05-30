# Trojan Horse Game — Rebuild Outline

A step-by-step process for rebuilding this project from scratch the right way.

---

## Phase 1 — Environment Setup

1. Create and activate a virtual environment
2. Install dependencies:
   - `fastapi` — the web framework
   - `uvicorn` — the server that runs FastAPI
   - `sqlalchemy` — the ORM (talks to the database)
   - `python-dotenv` — loads secrets from a `.env` file
   - `openai` — the LLM API client
3. Freeze dependencies into `requirements.txt`
4. Create a `.env` file for secrets (API keys, model provider setting)
5. Confirm `.gitignore` covers: `.env`, `.venv`, `__pycache__`, `*.db`

---

## Phase 2 — Project Structure

Set up the folder layout before writing any logic:

```
app/
  __init__.py      ← makes app/ a Python package
  models.py        ← database table definitions
  database.py      ← database connection + session
  game_logic.py    ← functions that interact with the DB
  llm_client.py    ← isolated module for calling the AI
  main.py          ← FastAPI app and routes
.env
requirements.txt
```

The order matters — each file depends on the one above it.

---

## Phase 3 — Models (`models.py`)

Define what gets stored in the database. Two tables:

- **GameSession** — represents one playthrough
  - Fields: id, guard_level, attempts_used, game_state
- **ChatMessage** — represents one message in a session
  - Fields: id, session_id (foreign key → GameSession), role, content

Standard practice: define a `Base` object here that both models inherit from.

---

## Phase 4 — Database Connection (`database.py`)

Three things this file needs to do:
1. Create the database engine (points to the `.db` file)
2. Create a `SessionLocal` factory (used to open DB sessions)
3. Define a `get_db` function — a FastAPI dependency that opens a session, yields it to a route, then closes it cleanly

Also call `Base.metadata.create_all(engine)` here to actually create the tables on startup.

---

## Phase 5 — Game Logic (`game_logic.py`)

Plain functions — no FastAPI stuff here, just database operations. Each function takes `db` as a parameter (passed in from the route).

- `create_game_session(db)` — inserts a new GameSession row, returns it
- `save_message(db, session_id, role, content)` — inserts a ChatMessage row, returns it
- `get_messages(db, session_id)` — fetches all messages for a session in order

Keeping this separate from `main.py` means the logic is testable and reusable.

---

## Phase 6 — LLM Client (`llm_client.py`)

Isolated module — nothing in here should know about FastAPI or the database.

- Read `MODEL_PROVIDER` from `.env` to decide which API to call
- Define a public `get_ai_response(messages, system_prompt)` function
- Internally, have a private `_openai_response(...)` function that handles the actual API call
- Format messages correctly before sending (system prompt goes first)

Keeping it isolated means you can swap providers later without touching any other file.

---

## Phase 7 — Routes (`main.py`)

Wire everything together here. Two routes:

- `POST /session` — calls `create_game_session`, returns the new session id
- `POST /chat` — accepts `session_id` + `message`, runs the full loop:
  1. Save the user message
  2. Fetch full message history for the session
  3. Send history to the LLM with a system prompt
  4. Save the AI response
  5. Return the AI response

Use `Depends(get_db)` on every route that needs the database — don't create sessions manually.

---

## Order to Build In

```
models → database → game_logic → llm_client → main
```

Test each layer before moving to the next. You can test routes with `uvicorn app.main:app --reload` and hit endpoints manually.
