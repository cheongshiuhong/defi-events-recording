# Standard libraries

# 3rd party libraries
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import Response, HTMLResponse

templates = Jinja2Templates(directory="src/templates")

home_router = APIRouter()


@home_router.get("/", response_class=HTMLResponse)
async def get_home(request: Request) -> Response:
    """
    Endpoint to return the home page html response.

    Args:
        request: The request which we shall not use.

    Returns:
        The templated html response.
    """
    return templates.TemplateResponse("index.html", {"request": request})
