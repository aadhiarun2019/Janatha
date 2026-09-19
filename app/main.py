from fastapi import FastAPI

app = FastAPI(title="Janatha Library")


@app.get("/")
def home():
    return {"message": "Janatha Library API is running"}