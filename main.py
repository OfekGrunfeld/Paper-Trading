import uvicorn
from fastapi import FastAPI

from utils.constants import HOST_IP, HOST_PORT 
from data.database import create_all_databases

from routes import stocks_router, users_router

def run_app(app: FastAPI) -> None:
    uvicorn.run(
        app,
        host=HOST_IP,
        port=int(HOST_PORT),
        ssl_keyfile="./key.pem", 
        ssl_certfile="./cert.pem",
    )

if __name__ == "__main__":
    papertrading_app = FastAPI()
    papertrading_app.include_router(stocks_router)
    papertrading_app.include_router(users_router)

    create_all_databases()
    run_app(app=papertrading_app)