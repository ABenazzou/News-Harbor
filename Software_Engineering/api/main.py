from fastapi import FastAPI 
from dotenv import dotenv_values
from motor.motor_asyncio import AsyncIOMotorClient
from routes import articles_router, categories_router
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    connection_string = config["connection_string"]
    tls = config["tlsClientCertificate"]
    tlsCA = config["tlsCA"]
    
    app.mongodb_client = AsyncIOMotorClient(
        connection_string, 
        tls=True, 
        tlsCertificateKeyFile=tls, 
        tlsCAFile=tlsCA, 
        tlsAllowInvalidCertificates=True
    )
    app.database = app.mongodb_client[config["db_name"]]

    yield 

    # Shutdown 
    app.mongodb_client.close()


config = dotenv_values(".env")

app = FastAPI(lifespan=lifespan)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    
app.include_router(articles_router, tags=["articles"])
app.include_router(categories_router, tags=["categories"])

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, port=int(config["port"]), host=config["host"])