from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
import re

from app.database import get_db
from app.game_logic import*
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
    #Find out where the player is 
    current_game=get_game_session(db,request.session_id)
    #Find out what day and guard lvl we are currently at
    day=current_game.day
    new_message=save_message(db,session_id=current_game.id,role="user",content=request.message,day=current_game.day,guard_level=current_game.guard_level)
    key_points=get_key_point(db, session_id=current_game.id, guard_level=current_game.guard_level)
    history=get_current_messages(db,session_id=current_game.id,day=current_game.day,guard_level=current_game.guard_level)
    format_history=[{"role": c.role, "content" :c.content} for c in history]
    guard_prompt=build_guard_prompt(guard_level=current_game.guard_level, day=current_game.day, key_points=key_points)
    reply=get_ai_response(format_history,system_prompt=guard_prompt)
    pattern=re.compile(r'\[KEYPOINT:\s+(.+)')
    if reply:
        new_key_points=pattern.findall(reply)

        if new_key_points:
            print("WHASSU")
            print(new_key_points)
            

            
            for point in new_key_points:
                print("LOOOOK HERE")
                print(point)
                clean_point=point.replace("]",'')
                save_key_points(db,session_id=current_game.id, guard_level=current_game.guard_level,day=current_game.day,content=clean_point)
        

    
        reply=re.sub(pattern,"",reply)
    ai_message=save_message(db,session_id=current_game.id, role="assistant", content=reply, day=current_game.day, guard_level=current_game.guard_level)
    return {"reply":reply}
    

#save the players message

    
