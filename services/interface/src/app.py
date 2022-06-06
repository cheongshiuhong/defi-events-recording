# 3rd party libraries
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Code
from .routers.v1 import v1_router

# Load the environment
load_dotenv()


app = FastAPI(openapi_url="/api/openapi.json", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
