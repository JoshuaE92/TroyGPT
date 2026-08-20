
from app.models import GameSession
from app.models import ChatMessage
from app.models import KeyPoint
from sqlalchemy import select
from app.guards import GUARD_PROMPTS, TOKEN_RULES, WORLD_CONTEXT, CONVERSATION_CONDUCT, CAPTAIN_PROMPT, GUARD_GREETINGS
def create_game_session(db):
    new_session=GameSession()
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def save_message(db,session_id,role,content,day,guard_level):
    new_message=ChatMessage(session_id=session_id, role=role,content=content,day=day,guard_level=guard_level)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

def get_messages(db,session_id):
    statement=select(ChatMessage).where(ChatMessage.session_id==session_id).order_by(ChatMessage.id)
    return db.scalars(statement).all()

def get_current_messages(db,session_id,day,guard_level):
    statement=select(ChatMessage).where(ChatMessage.session_id==session_id).where(ChatMessage.day==day).where(ChatMessage.guard_level==guard_level).order_by(ChatMessage.id)
    return db.scalars(statement).all()

def save_key_points(db,session_id,guard_level,day,content):
     new_key_point=KeyPoint(session_id=session_id,guard_level=guard_level , day=day, content=content)
     db.add(new_key_point)
     db.commit()
     db.refresh(new_key_point)
     return new_key_point

def get_key_point(db,session_id,guard_level):
    key_point=select(KeyPoint).where(KeyPoint.session_id==session_id).where(KeyPoint.guard_level==guard_level).order_by(KeyPoint.id)
    return db.scalars(key_point).all()

def build_guard_prompt(guard_level, day, key_points):
    base=WORLD_CONTEXT + "\n\n" + GUARD_PROMPTS[guard_level]["base_prompt"] + CONVERSATION_CONDUCT

    notes="\n".join(f"-{kp.content}" for kp in key_points)

    if day==2:
        base+="\n\nThis person has been to the city gate before. This is the SECOND day they have shown up trying to get in — they were turned back yesterday. Word of repeat visitors travels among the guards, so be noticeably more suspicious than usual. Do not take their answers at face value; press harder on anything vague."
    if day==3:
        base+="\n\nThis is the THIRD day this person has shown up at the city gate, and they have already been turned back twice. A third attempt after two rejections is a serious red flag. Be as analytical and strict as possible: actively hunt for any contradiction with what they have claimed on previous days, treat even small inconsistencies as disqualifying, and assume they are hiding something."

    if key_points:
        base += "\n\nNOTES FROM PRIOR ENCOUNTERS (reference these to catch inconsistencies):\n" + notes


    base+=TOKEN_RULES

    return base

def get_game_session(db,session_id):
    statement=select(GameSession).where(GameSession.id==session_id)
    return db.scalar(statement)

def build_eva_response(key_points,history):
    notes="\n".join(f"-{kp.content}" for kp in key_points)
    base=WORLD_CONTEXT + "\n\n" + CAPTAIN_PROMPT["base_prompt"]+notes


    if key_points:
        base+="\n\nNOTES FROM PRIOR ENCOUNTERS (reference these to point out to the user where they went wrong):\n" + notes
    return base

def build_closing_prompt(guard_level, outcome):
    base = GUARD_PROMPTS[guard_level]["base_prompt"]

    if outcome == "CONVINCED":
        base += """
---
THE CONVERSATION IS OVER. The player has fully convinced you, and you are letting them and their large gift through the gate.

Write ONE final message, in character:
- Warmly and naturally tell them you're satisfied and are opening the gate for them.
- You may briefly nod to the detail that won you over (the story they told, the reason for the gift).
- This is goodbye — do NOT ask any further questions or invite more discussion.
- Speak ONLY in-character dialogue. Do NOT output any notes, brackets, DELTA, KEYPOINT, ==== lines, or system tokens of any kind.
"""

    if outcome == "DENIED":
        base += """
---
THE CONVERSATION IS OVER. You are NOT convinced, and you are turning the player away right now. The gate stays shut.

Write ONE final message, in character:
- Firmly and decisively tell them that they and their gift may not enter today.
- You may briefly state what left you unconvinced, but do not argue or negotiate.
- Do NOT let them through, and do NOT leave the door open for more attempts in this conversation.
- Speak ONLY in-character dialogue. Do NOT output any notes, brackets, DELTA, KEYPOINT, ==== lines, or system tokens of any kind.
"""

    return base


def get_gaurd_greeting(day,guard):
    greeting=GUARD_GREETINGS[guard][day]
    return greeting


