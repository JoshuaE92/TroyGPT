"""Read-only peek at game.db — sessions, messages, and keypoints.

Usage:
    python peek_db.py         # list all sessions, then detail the most recent one
    python peek_db.py 5       # full detail (messages + keypoints) for session 5
"""
import os
import sqlite3
import sys

DB = os.path.join(os.path.dirname(__file__), "game.db")


def main():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    print("=== GAME SESSIONS (newest first) ===")
    sessions = cur.execute("SELECT * FROM game_session ORDER BY id DESC").fetchall()
    for s in sessions:
        print(f"  #{s['id']:>3}  guard {s['guard_level']}  day {s['day']}  "
              f"conviction {s['conviction']:>3}  state {s['game_state']}")
    if not sessions:
        print("  (no sessions yet)")
        return

    sid = int(sys.argv[1]) if len(sys.argv) > 1 else sessions[0]["id"]

    print(f"\n=== SESSION {sid} — MESSAGES ===")
    rows = cur.execute("SELECT * FROM chat_message WHERE session_id=? ORDER BY id", (sid,)).fetchall()
    for m in rows:
        print(f"  [day {m['day']} · guard {m['guard_level']}] {m['role']}: {m['content'][:110]}")
    if not rows:
        print("  (no messages)")

    print(f"\n=== SESSION {sid} — KEYPOINTS ===")
    rows = cur.execute("SELECT * FROM key_point WHERE session_id=? ORDER BY id", (sid,)).fetchall()
    for k in rows:
        print(f"  [guard {k['guard_level']} · day {k['day']}] {k['content']}")
    if not rows:
        print("  (no keypoints)")

    con.close()


if __name__ == "__main__":
    main()
