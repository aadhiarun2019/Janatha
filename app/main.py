from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.routes.public import router as public_router
from app.routes.auth import router as auth_router

from fastapi.responses import RedirectResponse

app = FastAPI(title="Janatha Library")


# Session support for admin login
app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-later"
)


# Serve static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# Jinja templates
templates = Jinja2Templates(
    directory="templates"
)


# API routes
app.include_router(public_router)
app.include_router(auth_router)


# Homepage
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@app.get("/admin")
def admin_page(request: Request):
    if "admin_id" not in request.session:
        return RedirectResponse("/")

    return templates.TemplateResponse(
        request=request,
        name="admin.html"
    )