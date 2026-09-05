/* =========================================================================
   The Gate of Troy — front-end logic (vanilla JS).

   Ported from the Claude Design reference implementation, with its STUBS
   replaced by real calls to the FastAPI backend:
       POST /session            -> { session_id }
       GET  /session_id/{id}     -> { greeting }
       POST /chat  {id, message} -> { reply, conviction, status, day, guard_level, recap? }

   NOTE (for Josh, later): this is the file you wanted to rewrite by hand as a
   learning exercise. The highest-value parts to redo yourself are handleChat()
   (the status -> screen state machine) and the event wiring at the bottom.
   ========================================================================= */

// ---- static copy (front-end only; no reason to spend an API call on these) ----
const GUARDS = {
  1: { name: "Guard Barnaby", title: "of the outer gate — friendly, and far too trusting" },
  2: { name: "Guard Cassius", title: "of the second gate — stern, and by the book" },
  3: { name: "Captain Livia", title: "of the inner gate — paranoid, and never wrong" },
};

const PORTRAITS = ["/static/images/barnaby.png", "/static/images/cassius.png", "/static/images/livia.png"];

const BRIEFING = [
  "*checks the ropes on the horse one last time* Right. Listen, because I will only lay it out once. That is our horse, and inside it are our men, and the only thing standing between them and the inside of Troy is your mouth.",
  "*counts on her fingers* Three gates. Three guards, and each one harder than the last. Barnaby will believe almost anything. Cassius believes documents. Livia believes nothing at all.",
  "You get three days at each gate. Talk to your guard, answer what he asks, and keep his conviction climbing — if it hits the floor, he sends you home and the day is gone.",
  "*puts a hand on your shoulder* One more thing, and it matters most: they remember. Whatever you tell one guard, tell the next the same. A story that changes is a story that gets you killed.",
  "That's the whole of it. Go on — it's a long walk up the hill.",
];

const ROLLS = {
  approach: {
    1: ["The road to Troy runs uphill and does not hurry.", "Behind you, the horse creaks on its rollers.", "At the first gate, a guard raises his lamp."],
    2: ["Word travels faster than a wooden horse.", "The second gate is smaller, and better watched.", "A guard is already waiting for you."],
    3: ["Past the second wall, the city breathes on you.", "The last gate is barely a gate at all — a corridor of spears.", "A captain steps into the lamplight."],
  },
  retreat: ["The gate closes behind you.", "You hurry back to camp before the light comes.", "Eva is awake. Eva is always awake."],
  night: ["Night. Then another day at the same gate."],
};

const FALLBACK_GREETING = "*regards you and your enormous horse* ...State your business, traveler.";
const DEBRIEF_FALLBACK = ["*hands you water* Come find me after your next attempt — I couldn't gather my notes in time. Keep your story straight, and keep it calm."];
const WIN_BODY = "Three guards, three stories, one gate at a time. The horse stands in the square and the city has gone to bed. Whatever happens next is no longer a matter of persuasion.";
const LOSE_BODY = "Three days at the same gate and the same guard, and nothing you said held together long enough to move him. Eva has already started writing the report.";

const TYPE_SPEED = 20; // ms per character

// ---- state ----
const state = {
  screen: "title", sessionId: null,
  day: 1, level: 1, conviction: 50, gatesPassed: 0,
  outcome: null, recap: "", debriefDay: 1,
  busy: false, log: [],
  evaLines: [], evaIndex: 0, evaBusy: false, evaAfter: null,
  rollAfter: null, _rollTimer: null,
};

// ---- tiny helpers ----
const el = (id) => document.getElementById(id);
function splitAction(text) {
  const m = text.match(/^\*(.+?)\*\s*/);
  return m ? [m[1], text.slice(m[0].length)] : ["", text];
}
function show(name) {
  ["title", "eva", "roll", "gate", "end"].forEach((s) => el("screen-" + s).classList.add("is-hidden"));
  el("screen-" + name).classList.remove("is-hidden");
  el("ledger").classList.add("is-hidden");
  state.screen = name;
}
function setInputEnabled(on) {
  el("player-input").disabled = !on;
  el("send-btn").disabled = !on;
}

// ---- typewriter ----
function typewriter(spanEl, caretEl, full, onDone) {
  clearInterval(spanEl._timer);
  spanEl.textContent = "";
  caretEl.textContent = "█";
  let i = 0;
  spanEl._timer = setInterval(() => {
    i++;
    spanEl.textContent = full.slice(0, i);
    if (i >= full.length) {
      clearInterval(spanEl._timer);
      caretEl.textContent = "";
      if (onDone) onDone();
    }
  }, TYPE_SPEED);
}

// ---- guard dialogue ----
function say(speaker, text) {
  const [action, spoken] = splitAction(text);
  el("speaker-name").textContent = speaker;
  el("speaker-title").textContent = speaker === "You" ? "traveler at the gate" : GUARDS[state.level].title;
  el("stage-direction").textContent = action;
  state.log.push({ who: speaker, text: spoken, stamp: `Day ${state.day} · Gate ${state.level}` });
  typewriter(el("spoken-text"), el("caret"), spoken);
}

// ---- conviction meter + locked row ----
function paintConviction(v) { // update the meter display only
  el("conviction-num").textContent = v;
  el("conviction-fill").style.width = v + "%";
}
function setConviction(v) { // update the meter AND the stored value
  state.conviction = v;
  paintConviction(v);
}
function setLocked(isLocked, label) {
  el("input-row").classList.toggle("is-hidden", isLocked);
  el("locked-row").classList.toggle("is-hidden", !isLocked);
  if (label) el("outcome-btn").textContent = label;
}

// ---- Eva (briefing + debrief) ----
function updateEvaCue() {
  el("eva-cue").textContent = state.evaBusy ? "Skip" : (state.evaIndex >= state.evaLines.length - 1 ? "Okay" : "Continue");
}
function startEva(lines, kicker) {
  state.evaLines = lines;
  state.evaIndex = 0;
  el("eva-kicker").textContent = kicker;
  typeEva(lines[0]);
}
function typeEva(text) {
  const [action, spoken] = splitAction(text);
  el("eva-action").textContent = action;
  state.evaBusy = true;
  updateEvaCue();
  typewriter(el("eva-spoken"), el("eva-caret"), spoken, () => { state.evaBusy = false; updateEvaCue(); });
}
function evaNext() {
  if (state.evaBusy) { // skip to full line
    const spanEl = el("eva-spoken");
    clearInterval(spanEl._timer);
    spanEl.textContent = splitAction(state.evaLines[state.evaIndex])[1];
    el("eva-caret").textContent = "";
    state.evaBusy = false;
    updateEvaCue();
    return;
  }
  const next = state.evaIndex + 1;
  if (next < state.evaLines.length) { state.evaIndex = next; typeEva(state.evaLines[next]); return; }
  // reached the end of Eva's lines
  if (state.evaAfter === "approach") return roll(ROLLS.approach[state.level], "gate");
  if (state.evaAfter === "nightgate") return roll(ROLLS.night, "gate");
  enterGate();
}

// ---- cinematic roll ----
function roll(lines, after) {
  state.rollAfter = after;
  show("roll");
  const box = el("roll-lines");
  box.innerHTML = "";
  lines.forEach((text, i) => {
    const d = document.createElement("div");
    d.textContent = text;
    d.style.cssText = "font-family:'Press Start 2P',monospace;font-weight:300;font-size:1.7cqw;line-height:1.9;color:#fff;letter-spacing:0.04em;opacity:0;animation:rollup 0.9s ease forwards;animation-delay:" + (0.35 + i * 1.25) + "s";
    box.appendChild(d);
  });
  clearTimeout(state._rollTimer);
  state._rollTimer = setTimeout(rollDone, 1400 + lines.length * 1300);
}
function rollDone() {
  clearTimeout(state._rollTimer);
  const after = state.rollAfter;
  state.rollAfter = null;
  if (after === "gate") return enterGate();
  if (after === "debrief") return startDebrief();
  if (after === "win") return endScreen(true);
  if (after === "lose") return endScreen(false);
}

// ---- entering / playing a gate ----
function enterGate() {
  show("gate");
  el("day-label").textContent = state.day;
  el("gate-label").textContent = ["I", "II", "III"][state.level - 1];
  el("gate-portrait").src = PORTRAITS[state.level - 1];
  setConviction(state.conviction);
  setLocked(false);
  greet();
}

async function greet() {
  setInputEnabled(false);
  try {
    const r = await fetch(`/session_id/${state.sessionId}`);
    const data = await r.json();
    say(GUARDS[state.level].name, data.greeting || FALLBACK_GREETING);
  } catch (e) {
    say(GUARDS[state.level].name, FALLBACK_GREETING);
  } finally {
    setInputEnabled(true);
    el("player-input").focus();
  }
}

async function send() {
  const text = el("player-input").value.trim();
  if (!text || state.busy) return;
  el("player-input").value = "";
  say("You", text);
  state.busy = true;
  setInputEnabled(false);
  try {
    const r = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, message: text }),
    });
    const data = await r.json();
    handleChat(data);
  } catch (e) {
    say(GUARDS[state.level].name, "*cups a hand to his ear* ...The wind swallowed that. Say it again?");
  } finally {
    state.busy = false;
    if (!state.outcome) { setInputEnabled(true); el("player-input").focus(); }
  }
}

// ---- the status -> screen state machine (the core game logic) ----
function handleChat(data) {
  const status = data.status || "PLAYING";

  if (status === "PLAYING") {
    if (typeof data.conviction === "number") setConviction(data.conviction);
    say(GUARDS[state.level].name, data.reply || "...");
    return;
  }
  // On a transition the backend already reset conviction to 50 for the NEXT round.
  // Don't snap the bar to that 50 now (the confusing "went up when I lost" jump).
  // Instead show the OUTCOME (full on a win, empty on a loss) during the closing,
  // and stash the reset value so enterGate() shows it fresh next round.
  if (typeof data.conviction === "number") state.conviction = data.conviction;
  paintConviction(status === "CONVINCED" || status === "WON" ? 100 : 0);
  if (status === "CONVINCED") {
    say(GUARDS[state.level].name, data.reply); // current guard opens the gate
    state.gatesPassed = state.level;
    state.level = data.guard_level || state.level + 1; // backend is the source of truth
    state.day = data.day || 1;
    state.outcome = "pass";
    setLocked(true, "Approach gate " + ["I", "II", "III"][state.level - 1]);
    return;
  }
  if (status === "WON") {
    say(GUARDS[state.level].name, data.reply);
    state.gatesPassed = 3;
    state.outcome = "win";
    setLocked(true, "Take the horse inside");
    return;
  }
  if (status === "DENIED") {
    say(GUARDS[state.level].name, data.reply);
    state.recap = data.recap || "";
    state.debriefDay = (data.day || 2) - 1; // backend already advanced the day
    state.day = data.day || state.day + 1;
    state.outcome = "fail";
    setLocked(true, "Head back to camp");
    return;
  }
  if (status === "LOSE") {
    say(GUARDS[state.level].name, data.reply);
    state.recap = data.recap || "";
    state.outcome = "lose";
    setLocked(true, "Head back to camp");
    return;
  }
}

// ---- what the "continue" button does after an outcome ----
function outcomeGo() {
  const o = state.outcome;
  state.outcome = null;
  if (o === "pass") return roll(ROLLS.approach[state.level], "gate");
  if (o === "win") return endScreen(true);
  if (o === "fail") return roll(ROLLS.retreat, "debrief");
  if (o === "lose") return roll(ROLLS.retreat, "lose");
}

function startDebrief() {
  show("eva");
  state.evaAfter = "nightgate";
  startEva(buildDebriefLines(state.recap), "Debrief — end of day " + state.debriefDay);
}
function buildDebriefLines(recap) {
  if (!recap) return DEBRIEF_FALLBACK;
  const lines = recap.split("\n").map((l) => l.replace(/\*\*/g, "").replace(/^[-*]\s+/, "").trim()).filter(Boolean);
  return lines.length ? lines : DEBRIEF_FALLBACK;
}

function endScreen(won) {
  show("end");
  el("end-kicker").textContent = won ? "The horse is inside the walls" : "Turned away";
  el("end-title").textContent = won ? "Troy sleeps behind you" : "The gate stays shut";
  el("end-body").textContent = won ? WIN_BODY : LOSE_BODY;
  el("stat-days").textContent = won ? 3 : state.day;
  el("stat-gates").textContent = won ? 3 : state.gatesPassed;
}

// ---- ledger (conversation log) ----
function renderLedger() {
  const list = el("ledger-list");
  list.innerHTML = "";
  state.log.slice().reverse().forEach((entry) => {
    const row = document.createElement("div");
    row.style.cssText = "padding:1.8cqh 0;border-bottom:1px solid rgba(234,233,233,0.1);display:flex;flex-direction:column;gap:0.6cqh";
    row.innerHTML =
      '<div style="display:flex;justify-content:space-between;align-items:baseline">' +
        '<span style="font-family:\'Press Start 2P\',monospace;font-size:0.8cqw;letter-spacing:0.12em;text-transform:uppercase;color:#e1ad66"></span>' +
        '<span style="font-size:0.85cqw;color:rgba(234,233,233,0.35);font-feature-settings:\'tnum\'"></span>' +
      '</div>' +
      '<div style="font-size:1.4cqw;line-height:1.45;color:rgba(234,233,233,0.8);text-align:left"></div>';
    row.querySelectorAll("span")[0].textContent = entry.who;
    row.querySelectorAll("span")[1].textContent = entry.stamp;
    row.querySelector("div:last-child").textContent = entry.text;
    list.appendChild(row);
  });
}

// ---- start / restart ----
async function begin() {
  state.day = 1; state.level = 1; state.conviction = 50; state.gatesPassed = 0;
  state.outcome = null; state.log = [];
  try {
    const r = await fetch("/session", { method: "POST" });
    const data = await r.json();
    state.sessionId = data.session_id;
  } catch (e) {
    // If the session call fails we still show the briefing; the gate will retry.
  }
  show("eva");
  state.evaAfter = "approach";
  startEva(BRIEFING, "Briefing — the night before");
}
function restart() {
  [el("spoken-text"), el("eva-spoken")].forEach((s) => clearInterval(s._timer));
  clearTimeout(state._rollTimer);
  show("title");
}

// ---- event wiring ----
el("begin-btn").addEventListener("click", begin);
el("send-btn").addEventListener("click", send);
el("player-input").addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
el("ledger-btn").addEventListener("click", () => { renderLedger(); el("ledger").classList.remove("is-hidden"); });
el("ledger-close").addEventListener("click", () => el("ledger").classList.add("is-hidden"));
el("eva-box").addEventListener("click", evaNext);
el("outcome-btn").addEventListener("click", outcomeGo);
el("restart-btn").addEventListener("click", restart);
el("screen-roll").addEventListener("click", rollDone);
