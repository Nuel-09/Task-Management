import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import ASCENDING

from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo, get_database
from app.models.todo import TODOS_COLLECTION
from app.models.user import USERS_COLLECTION
from app.routers.auth import router as auth_router
from app.routers.todos import router as todos_router

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    is_testing = os.getenv("TESTING") == "1"
    if not is_testing:
        await connect_to_mongo()
        db = get_database()
        await db[USERS_COLLECTION].create_index("email", unique=True)
        await db[TODOS_COLLECTION].create_index([("user_id", ASCENDING), ("status", ASCENDING)])
    try:
        yield
    finally:
        if not is_testing:
            await close_mongo_connection()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

app.include_router(auth_router)
app.include_router(todos_router)


def render_template(request: Request, template_name: str) -> HTMLResponse:
    context = {
        "request": request,
        "app_name": settings.app_name,
    }
    # Starlette changed TemplateResponse signature in newer releases.
    try:
        return templates.TemplateResponse(
            request=request,
            name=template_name,
            context=context,
        )
    except TypeError:
        return templates.TemplateResponse(template_name, context)


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return render_template(request, "login.html")


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return render_template(request, "register.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return render_template(request, "dashboard.html")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
