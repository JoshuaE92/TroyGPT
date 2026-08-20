import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client=OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",

)



def get_ai_response(messages,system_prompt):
    formatted=[{"role":"system","content":system_prompt}]+messages
    try:
        response=client.chat.completions.create(
            model="openai/gpt-oss-20b",
                    messages=formatted,

        )
    except Exception:
        return None
    return response.choices[0].message.content