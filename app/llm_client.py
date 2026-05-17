import os
from dotenv import load_dotenv

load_dotenv()

MODEL_PROVIDER=os.getenv("Model_Provider","openai")

def get_ai_response(messages: list, system_prompt:str)->str:
    if MODEL_PROVIDER=="openai":
        return _openai_response(messages,system_prompt)
    else:
        raise ValueError(f"Unsoported MODEL_PROVIDER: {MODEL_PROVIDER}")

def _openai_response(messages: list,system_prompt:str)->str:
   
    from openai import OpenAI
    client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    formatted=[{"role":"system","content":system_prompt}]
    for msg in messages:
        formatted.append({"role": msg["role"],"content":msg["content"]})
    
    response=client.chat.completions.create(
        model="gpt-4o-mini",
        messages=formatted, #type:ignore
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content or ""


   
