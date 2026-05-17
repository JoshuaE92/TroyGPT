from fastapi import FastAPI
app=FastAPI()

@app.get("/")
def root():
    return{"message": "Trojan Horse Game API is running"}

