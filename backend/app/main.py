import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .database import Base, engine, SessionLocal
from .api import servers, checks, settings as settings_api
from .api import monitor, groups 
from .services.checker import run_single_check
from .services.telegram_bot import start_telegram_bot_loop
from .models import Server, SettingsModel


app = FastAPI(title=settings.PROJECT_NAME)


Base.metadata.create_all(bind=engine)


app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    session_cookie="v2rayscan_session",
    max_age=60 * 60 * 24,  
)

ROOT_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT_DIR / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"


def require_login(request: Request):

    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return True


protected = [Depends(require_login)]


app.include_router(
    servers.router,
    prefix="/api/servers",
    tags=["servers"],
    dependencies=protected,
)
app.include_router(
    checks.router,
    prefix="/api/checks",
    tags=["checks"],
    dependencies=protected,
)
app.include_router(
    settings_api.router,
    prefix="/api/settings",
    tags=["settings"],
    dependencies=protected,
)

app.include_router(
    groups.router,
    prefix="/api/groups",
    tags=["groups"],
    dependencies=protected,
)


app.include_router(monitor.router, prefix="/api/monitor")


def _render_login_page(error: Optional[str] = None) -> HTMLResponse:
    error_html = ""
    if error:
        error_html = f'<div class="error">{error}</div>'
    html = f"""
<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <title>v2rayscan - Login</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #0f172a;
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
        }}
        .card {{
            background: #111827;
            padding: 24px 28px;
            border-radius: 16px;
            box-shadow: 0 20px 25px -5px rgba(15,23,42,0.8);
            border: 1px solid #1f2937;
            width: 100%;
            max-width: 380px;
        }}
        h1 {{
            font-size: 1.2rem;
            margin: 0 0 10px;
            text-align: center;
        }}
        p.subtitle {{
            font-size: 0.8rem;
            margin: 0 0 16px;
            text-align: center;
            color: #9ca3af;
        }}
        .form-row {{
            display: flex;
            flex-direction: column;
            margin-bottom: 12px;
        }}
        label {{
            font-size: 0.8rem;
            margin-bottom: 4px;
        }}
        input[type="text"],
        input[type="password"] {{
            background: #020617;
            border-radius: 8px;
            border: 1px solid #1f2937;
            padding: 8px 10px;
            color: #e5e7eb;
            font-size: 0.9rem;
        }}
        input:focus {{
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px #1d4ed8;
        }}
        button {{
            width: 100%;
            margin-top: 8px;
            padding: 9px 0;
            border-radius: 8px;
            border: none;
            background: #3b82f6;
            color: white;
            font-weight: 600;
            font-size: 0.9rem;
            cursor: pointer;
        }}
        button:hover {{
            background: #2563eb;
        }}
        .error {{
            background: #7f1d1d;
            color: #fecaca;
            border-radius: 8px;
            padding: 8px 10px;
            font-size: 0.8rem;
            margin-bottom: 10px;
        }}
        .footer {{
            margin-top: 12px;
            text-align: center;
            font-size: 0.75rem;
            color: #6b7280;
        }}
        .lang-row {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 6px;
            margin-bottom: 8px;
            font-size: 0.8rem;
        }}
        .lang-row select {{
            background: #020617;
            border-radius: 6px;
            border: 1px solid #374151;
            color: #e5e7eb;
            padding: 3px 6px;
            font-size: 0.8rem;
        }}
    </style>
    <!-- i18n برای لاگین -->
    <script src="js/i18n.js"></script>
</head>
<body>
<div class="card">
    <h1 data-i18n="login.title"></h1>
    <p class="subtitle" data-i18n="login.subtitle"></p>

    <div class="lang-row">
        <label for="login-lang" data-i18n="login.language.label"></label>
        <select id="login-lang" class="lang-select">
            <option value="en" data-i18n="login.language.en"></option>
            <option value="fa" data-i18n="login.language.fa"></option>
        </select>
    </div>

    {error_html}
    <form method="post" action="/login">
        <div class="form-row">
            <label for="username" data-i18n="login.username"></label>
            <input id="username" name="username" type="text" autocomplete="username" autofocus>
        </div>
        <div class="form-row">
            <label for="password" data-i18n="login.password"></label>
            <input id="password" name="password" type="password" autocomplete="current-password">
        </div>
        <button type="submit" data-i18n="login.button"></button>
    </form>
    <div class="footer" data-i18n="login.footer">
        Use credentials from backend/.env (ADMIN_USERNAME / ADMIN_PASSWORD)
    </div>
</div>
</body>
</html>
"""
    return HTMLResponse(html)



@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):

    if request.session.get("user"):
        return RedirectResponse(url="/", status_code=302)
    return _render_login_page()


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if (
        username == settings.ADMIN_USERNAME
        and password == settings.ADMIN_PASSWORD
    ):
        request.session["user"] = username
        return RedirectResponse(url="/", status_code=302)


    return _render_login_page("نام کاربری یا رمز عبور اشتباه است.")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):

    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=302)

    if not INDEX_FILE.exists():
        raise HTTPException(status_code=500, detail="frontend/index.html not found")

    return FileResponse(INDEX_FILE)



if FRONTEND_DIR.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(FRONTEND_DIR), html=True),
        name="frontend",
    )


async def checker_loop():

    while True:
        db = SessionLocal()
        try:
            settings_row = (
                db.query(SettingsModel).filter(SettingsModel.id == 1).first()
            )
            interval = (
                settings_row.check_interval_seconds
                if settings_row and settings_row.check_interval_seconds
                else 30
            )
            if interval < 5:
                interval = 5

            servers = db.query(Server).filter(Server.enabled == True).all()
            for srv in servers:
                run_single_check(db, srv)
        finally:
            db.close()

        await asyncio.sleep(interval)


@app.on_event("startup")
async def on_startup():

    asyncio.create_task(checker_loop())

    start_telegram_bot_loop()
