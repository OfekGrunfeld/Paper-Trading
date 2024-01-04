from fastapi import FastAPI as FastAPI
import uvicorn as uv

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}