
from app.models import GameSession, ChatMessage #need to do these imports, they allow you to take in info from db

def create_gamesession(db):
    gamesession=GameSession()
    db.add(gamesession)
    db.commit()
    db.refresh(gamesession)#keeps db up to date
    return (gamesession)#

def save_message(db,session_id,role,content):
    chatmessage=ChatMessage(session_id=session_id,role=role,content=content)
    db.add(chatmessage)
    db.commit()
    db.refresh(chatmessage)
    return(chatmessage)

def get_messages(db,session_id):
    return db.query(ChatMessage).filter(ChatMessage.session_id==session_id).all()



