# from typing import Union
from fastapi import FastAPI 
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient
from routes import router as article_router
# import sys
import uvicorn

config = dotenv_values(".env")

app = FastAPI()

@app.on_event("startup")
def startup_db_client():
    
    connection_string = config["connection_string"]
    tls = config["tlsClientCertificate"]
    tlsCA = config["tlsCA"]
    
    app.mongodb_client = AsyncIOMotorClient(connection_string, tls=True, tlsCertificateKeyFile=tls, tlsCAFile=tlsCA, tlsAllowInvalidCertificates=True)
    app.database = app.mongodb_client[config["db_name"]]
    
    

@app.on_event("shutdown")
def shutdown_db_client():
    app.mongodb_client.close()
    
    
app.include_router(article_router, tags=["articles"])


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=int(config["port"]), host=config["host"])