from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.routes.public import router as public_router
from app.routes.auth import router as auth_router
from app.routes.uploads import router as upload_router


app = FastAPI(title="Janatha Library")


app.add_middleware(
    SessionMiddleware,
    secret_key="change-this-later"
)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

templates = Jinja2Templates(
    directory="templates"
)

app.include_router(public_router)
app.include_router(auth_router)
app.include_router(upload_router)


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


@app.get("/admin")
def admin_page(request: Request):
    if request.session.get("role") != "admin":
        return RedirectResponse("/")

    return templates.TemplateResponse(
        request=request,
        name="admin.html"
    )
