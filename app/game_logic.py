
from app.models import GameSession
from app.models import ChatMessage
from app.models import KeyPoint
from sqlalchemy import select

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



