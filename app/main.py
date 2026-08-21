from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import re

from app.database import get_db
from app.game_logic import*
from app.llm_client import get_ai_response
import time

from pydantic import BaseModel


app=FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("templates/index.html")

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
    if current_game.day:
        day=current_game.day
    new_message=save_message(db,session_id=current_game.id,role="user",content=request.message,day=current_game.day,guard_level=current_game.guard_level)
    key_points=get_key_point(db, session_id=current_game.id, guard_level=current_game.guard_level)
    history=get_current_messages(db,session_id=current_game.id,day=current_game.day,guard_level=current_game.guard_level)
    format_history=[{"role": c.role, "content" :c.content} for c in history]
    guard_prompt=build_guard_prompt(guard_level=current_game.guard_level, day=current_game.day, key_points=key_points)
    reply=get_ai_response(format_history,system_prompt=guard_prompt)
    print("HERE IS THE OG REPLY")
    print(reply)
   
   
    if reply:
        parts=re.split(r'=+', reply)
        pattern=re.compile(r'KEYPOINT:\s+(.+)')
        pattern2 = re.compile(r'DELTA:\s*([+-]?\d+)')

        

        if pattern and len(parts)>1:

            new_key_points=pattern.findall(parts[1])
            

            if new_key_points:
                print("WHASSU")
                print(new_key_points)
            

            
            for point in new_key_points:
                print("LOOOOK HERE")
                print(point)
              
                save_key_points(db,session_id=current_game.id, guard_level=current_game.guard_level,day=current_game.day,content=point)

        if pattern2 and len(parts)>1:
            delta=(pattern2.findall(parts[1]))

            for delt in delta:
                deltaint=int(delt)
                current_game.conviction+=deltaint
                current_game.conviction=max(0,min(current_game.conviction,100))

        status="PLAYING"

        if current_game.conviction>=100:
            closing=build_closing_prompt(guard_level=current_game.guard_level, outcome="CONVINCED")
            closing_message=get_ai_response(format_history,system_prompt=closing) or "*the guard studies you a long moment, then steps aside* ...Very well. You've said enough to satisfy me. The gate is open — pass through, and be on your way."
            ai_message=save_message(db,session_id=current_game.id, role="assistant", content=closing_message, day=current_game.day, guard_level=current_game.guard_level)
         

            

            if current_game.guard_level==3:
                current_game.game_state="WON"
                status="WON"

                
            else:
                current_game.guard_level+=1
    
                current_game.conviction=50
                current_game.day=1
                status="CONVINCED"
            db.commit()
            
            return {"reply":ai_message.content,"conviction":current_game.conviction,"status":status,"day":current_game.day,"guard_level":current_game.guard_level}
            


            



        if current_game.conviction<=0:
            closing=build_closing_prompt(guard_level=current_game.guard_level, outcome="DENIED")
            closing_message=get_ai_response(format_history,system_prompt=closing) or "*the guard shakes their head and holds their ground* No. Not today. Whatever that thing is, it stays outside my gate. Turn back."

            ai_message=save_message(db,session_id=current_game.id, role="assistant", content=closing_message, day=current_game.day, guard_level=current_game.guard_level)
            

            if current_game.day==3:
                current_game.game_state="LOSE"
                status="LOSE"
            else:
                current_game.day+=1
                current_game.conviction=50
                status="DENIED"
                
            db.commit()
            eva_prompt=build_eva_response(key_points=key_points,history=format_history)
            recap = get_ai_response([{"role": "user", "content": "How did I do? Give me my debrief."}],
                        system_prompt=eva_prompt)
            if not recap:
                for _ in range(2):
                    recap = get_ai_response([{"role": "user", "content": "How did I do? Give me my debrief."}],
                                            system_prompt=eva_prompt)
                    if recap:
                        break

                    time.sleep(1)
            recap=recap or "Come find me after your next attempt — I couldn't gather my notes in time."


            return {"reply":ai_message.content,"conviction":current_game.conviction,"status":status,"recap":recap,"day":current_game.day,"guard_level":current_game.guard_level}

    
        db.commit()   
        ai_message=save_message(db,session_id=current_game.id, role="assistant", content=parts[0].rstrip(), day=current_game.day, guard_level=current_game.guard_level)
        return {"reply":ai_message.content,"conviction":current_game.conviction,"status":status,"day":current_game.day,"guard_level":current_game.guard_level}
    else:
        return{"reply":"*the guard frowns, distracted for a moment* ...Hm? Say that again — I didn't quite catch you.","conviction":current_game.conviction,"status":"PLAYING","day":current_game.day,"guard_level":current_game.guard_level}


    

@app.get("/session_id/{session_id}")
def read_item(session_id:int,db:Session=Depends(get_db)): 
        game=get_game_session(db,session_id=session_id)
        greeting=get_gaurd_greeting(game.day,game.guard_level)
        return{"greeting":greeting}

    
