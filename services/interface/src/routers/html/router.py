# 3rd party libraries
from fastapi import APIRouter

# Code
from .home import home_router

html_router = APIRouter()

html_router.include_router(home_router)
