# 🐴 Trojan Horse Game

> Talk your way past the guards of Troy. You've rolled an enormous wooden "gift" up to the city gate — now convince the guards to let it through. They don't know what's inside. Yet.

An AI persuasion game built with **FastAPI** and an LLM. Each guard is a character you have to talk around; a hidden **conviction meter** tracks how much they trust you, and every answer you give nudges it up or down. Win over three escalating guards to get the horse inside — or get turned away and debriefed by your handler, Captain Eva, before you try again.

*(Working title — the name's still being decided.)*

### ▶️ [Play it live → troygpt.onrender.com](https://troygpt.onrender.com/)

> Hosted on Render's free tier — if it's been idle it may take ~30 seconds to wake up on the first load.

---

## How it plays

- You approach a **guard** at the gate and try to convince them your giant wooden horse is a harmless gift.
- Every message you send is judged by the guard. A calm, specific, consistent story earns trust; evasion, contradictions, absurd claims, or rudeness destroy it.
- A hidden **conviction meter** (0–100, starts at 50) moves each turn:
  - Hit **100** → the guard opens the gate. You advance to the **next, harder guard**.
  - Hit **0** → you're turned away for the day.
- You get **3 days (attempts) per guard**. Fail all three and it's game over. Between failures, **Captain Eva** debriefs you on exactly where you slipped up.
- Convince all **three guards** — Barnaby (trusting), Cassius (by-the-book), and Captain Livia (paranoid) — to win.

The guards **remember**. Come back a second or third day and they'll recognize you, and grow more suspicious each time.

---

## Tech stack

| Layer | Choice |
|---|---|
| API | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| Persistence | SQLAlchemy 2.0 ORM — Postgres (Neon) in production, SQLite locally |
| LLM | [Groq](https://groq.com/) via the OpenAI SDK (`openai/gpt-oss-20b`) |
| Validation | Pydantic |
| Frontend | Vanilla-JS single-page app (state machine) in `templates/` + `static/` |
| Hosting | [Render](https://render.com/) (web service) + [Neon](https://neon.tech/) (Postgres) |

---

## Architecture at a glance

A few principles the codebase follows:

- **Backend owns the truth, frontend owns the presentation.** The API returns *facts* (`status`, `conviction`, `day`, `guard_level`); the frontend decides which *screen* to show and reacts to those facts.
- **One choke point for the LLM.** Every model call flows through `get_ai_response` in [`app/llm_client.py`](app/llm_client.py).
- **AI for the dynamic, static text for the predictable.** The interrogation, the conviction/keypoint judgment, and Captain Eva's tailored debrief are AI-generated. Guard greetings, briefings, and win/lose copy are hardcoded — no reason to spend an API call on text that never changes.
- **Guard "memory."** As the guard talks, it privately logs **keypoints** (concerns/contradictions), which are fed back into later turns and into Eva's debrief so her advice is grounded in what actually went wrong.

---

## Project structure

```
app/
  main.py         # FastAPI app + routes (/session, /chat, /session_id/{id})
  models.py       # SQLAlchemy models: GameSession, ChatMessage, KeyPoint
  database.py     # engine, SessionLocal, get_db dependency
  game_logic.py   # DB helpers + prompt builders (guard, closing, Eva, greeting)
  guards.py       # guard personalities, world context, token rules, greetings
  llm_client.py   # get_ai_response — the single Groq call
run.py            # dev entrypoint (uvicorn)
requirements.txt
```

---

## Getting started

### 1. Prerequisites
- Python 3.11+
- A free [Groq API key](https://console.groq.com/)

### 2. Install
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your API key
Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```
> `.env` is gitignored — your key never gets committed. The key stays server-side only; never expose it in frontend code.

### 4. Run
```bash
python run.py
```
The API starts at **http://127.0.0.1:8000**. Interactive docs (great for poking at the endpoints) live at **http://127.0.0.1:8000/docs**.

---

## API

### `POST /session`
Starts a new game. Returns the session id you'll pass to every other call.
```json
// → 200
{ "session_id": 1 }
```

### `POST /chat`
Send a message to the current guard.
```json
// body
{ "session_id": 1, "message": "It's a gift of olive wood for the children's festival." }

// → 200
{
  "reply": "…the guard's in-character response…",
  "conviction": 65,
  "status": "PLAYING",
  "day": 1,
  "guard_level": 1
}
```
`status` is the signal the frontend reacts to:

| status | meaning |
|---|---|
| `PLAYING` | normal turn, keep talking |
| `CONVINCED` | guard won over → advanced to the next guard |
| `WON` | all three guards convinced 🎉 |
| `DENIED` | turned away → retry next day (includes a `recap` from Captain Eva) |
| `LOSE` | out of days, game over |

### `GET /session_id/{session_id}`
Returns the current guard's in-character greeting for the session's guard/day. A pure read — no LLM call.
```json
// → 200
{ "greeting": "*leans on his spear with an easy grin* Well met, traveler! …" }
```

---

## Data model

| Table | Holds |
|---|---|
| `game_session` | one playthrough — `guard_level`, `day`, `conviction`, `game_state` |
| `chat_message` | every message (player + guard), tagged with `day` + `guard_level` |
| `key_point` | the guard's private concerns, used for suspicion and Eva's debrief |

---

## Status & roadmap

**Working:** full game engine — sessions, per-guard conversations, conviction scoring, keypoint memory, convinced/denied/won/lost transitions with persistence, guard greetings, and Captain Eva's debrief. Graceful LLM error handling, a state-machine frontend (briefing → guard → debrief → win/lose), and a **live deployment** on Render backed by Postgres.

**Next:**
- [ ] Per-IP rate limiting on the LLM endpoints *(protect API credits on the public link)*
- [ ] Lightweight play analytics *(how far players get, where they stall)*
- [ ] Optional player accounts *(guest play stays the default — no login wall)*
- [ ] Retune conviction deltas back to normal pacing *(currently inflated in `guards.py` for faster testing / demo)*

---

*A learning project — built to explore FastAPI, ORMs, and designing a game around an LLM.*
