from typing import List
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class GameSession(Base):
    __tablename__="game_session"
    id: Mapped[int] = mapped_column(primary_key=True)
    guard_level: Mapped[int] = mapped_column(default=1)
    attempts_used:Mapped[int]=mapped_column(default=0)
    game_state: Mapped[str]=mapped_column(default="Playing")
    day:Mapped[int]=mapped_column(default=1)
    messages: Mapped[List["ChatMessage"]]=relationship()



class ChatMessage(Base):
     __tablename__="chat_message"
     #id, tie to gamesession, message and who sent it, message and content, 

     id:Mapped[int]=mapped_column(primary_key=True)
     guard_level: Mapped[int] = mapped_column(default=1)
     day:Mapped[int]=mapped_column(default=1)
     session_id:Mapped[int]=mapped_column(ForeignKey("game_session.id"))
     role: Mapped[str]=mapped_column()
     content:Mapped[str]=mapped_column()


class KeyPoint(Base):
    __tablename__="key_point"
    id:Mapped[int]=mapped_column(primary_key=True)
    guard_level: Mapped[int] = mapped_column(default=1)
    session_id:Mapped[int]=mapped_column(ForeignKey("game_session.id"))
    day:Mapped[int]=mapped_column(default=1)
    content:Mapped[str]=mapped_column()
    

    

