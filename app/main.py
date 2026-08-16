from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.game_logic import create_game_session, save_message, get_messages 
from app.llm_client import get_ai_response
from pydantic import BaseModel


app=FastAPI()

class Chat(BaseModel):
    session_id: int
    message:str


@app.post("/session")
def new_session(db:Session=Depends(get_db)):
    game=create_game_session(db)
    return{"session_id":game.id}

@app.post("/chat")
def chat(request: Chat, db: Session=Depends(get_db)):
    new_message=save_message(db,request.session_id,role="user",content=request.message)
    history=get_messages(db,request.session_id)
    format_history=[{"role": c.role, "content" :c.content} for c in history]
    reply=get_ai_response(format_history,system_prompt="Say whatsup to the user")

   

    new_message=save_message(db,request.session_id,role="assistant",content=reply)
    return {"reply":reply}
    

#save the players message

    
