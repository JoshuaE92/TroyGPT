
from app.models import GameSession
from app.models import ChatMessage
from app.models import KeyPoint
from sqlalchemy import select
from app.guards import GUARD_PROMPTS, TOKEN_RULES
def create_game_session(db):
    new_session=GameSession()
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def save_message(db,session_id,role,content):
    new_message=ChatMessage(session_id=session_id, role=role,content=content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message

def get_messages(db,session_id):
    statement=select(ChatMessage).where(ChatMessage.session_id==session_id).order_by(ChatMessage.id)
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
    base=GUARD_PROMPTS[guard_level]["base_prompt"]

    notes="\n".join(f"-{kp.content}" for kp in key_points)

    if day==2:
        base+="\n\nYou have seen this exact person before. This is their SECOND day trying to get past you — you turned them away yesterday. Be noticeably more suspicious than usual. Do not take their answers at face value; press harder on anything vague."
    if day==3:
        base+="\n\nThis is the THIRD day this person has come to your gate, and you have already denied them twice. Be as analytical and strict as possible: actively hunt for any contradiction between what they say now and what they have claimed before. Treat even small inconsistencies as disqualifying, and assume they are hiding something."

    if key_points:
        base += "\n\nNOTES FROM PRIOR ENCOUNTERS (reference these to catch inconsistencies):\n" + notes


    base+=TOKEN_RULES

    return base





