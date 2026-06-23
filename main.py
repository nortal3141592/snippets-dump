from contextlib import asynccontextmanager
from routers import users, notes

from fastapi import FastAPI, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from database import engine, Base
from limiter import limiter


# rate limiting imports

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# exception handling
# from starlette.exceptions import HTTPException as StarletteHTTPException
# from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
# from fastapi.exceptions import RequestValidationError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

    await engine.dispose()

app = FastAPI(lifespan=lifespan)

templates = Jinja2Templates(directory="Templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# doing some rate limiting stuff
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(notes.router, prefix="/api/notes", tags = ["notes"])


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/register")
async def register(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.get("/create")
async def create(request: Request):
    return templates.TemplateResponse(request, "create.html")

@app.get("/notes/{note_id}")
async def note_page(request: Request, note_id: int):
    return templates.TemplateResponse(
        request,
        "note.html",
        {
            "request": request,
            "note_id": note_id,
        }
    )

@app.get("/profile")
async def profile(request: Request):
    return templates.TemplateResponse(request, "profile.html")

@app.get("/error")
async def error(request: Request, error_code: int = 500, error_message: str = "Something went wrong"):
    return templates.TemplateResponse(request, "error.html")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {"request": request, "error_code": exc.status_code, "error_message": exc.detail},
        status_code=exc.status_code
    )