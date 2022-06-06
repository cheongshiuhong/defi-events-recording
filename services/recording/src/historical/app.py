# 3rd party libraries
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Code
from .tasks.router import task_router


app = FastAPI(openapi_url="/api/rpc/openapi.json", docs_url="/api/rpc/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(task_router, prefix="/api/rpc/v1/tasks")
