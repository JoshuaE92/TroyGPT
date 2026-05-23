from fastapi import FastAPI
from fastapi import Depends
from app.database import get_db
from app.game_logic import get_messages, create_gamesession, save_message
from pydantic import BaseModel
from app.llm_client import get_ai_response
app=FastAPI()

class ChatRequest(BaseModel):
    session_id:int
    message:str


@app.get("/")
def root():
    return{"message": "Trojan Horse Game API is running"}

@app.post("/session")
def route(db=Depends(get_db)):
    game_session=create_gamesession(db)
    return {"session_id":game_session.id}

