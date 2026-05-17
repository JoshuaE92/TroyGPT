from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base
Base=declarative_base()

class GameSession(Base):
    __tablename__="game_session"
    id= Column(Integer,primary_key=True)
    guard_level= Column(Integer,default=1)
    attempts_used= Column(Integer,default=0)
    game_state= Column(String, default="playing")

class ChatMessage(Base):
    __tablename__="chat_message"
    id= Column(Integer,primary_key=True)
    session_id=Column(Integer, ForeignKey("game_session.id"))
    role=Column(String,default="user")
    content=Column(String)
    
