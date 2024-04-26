import uvicorn
from fastapi import FastAPI

from utils.constants import HOST_IP, HOST_PORT 
from data.database import initialise_all_databases

from routes.routes import fastapi_router

def run_app(app: FastAPI) -> None:
    uvicorn.run(
        app,
        host=HOST_IP,
        port=int(HOST_PORT),
        ssl_keyfile="./https/key.pem", 
        ssl_certfile="./https/cert.pem",
    )

if __name__ == "__main__":
    papertrading_app = FastAPI()
    papertrading_app.include_router(fastapi_router)

    if initialise_all_databases():
        run_app(app=papertrading_app)
        