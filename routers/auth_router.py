import logging
import time
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from model.user_model import (
    create_user,
    get_user_by_login
)
from utils.security import pwd_context
from utils.template import render

router = APIRouter(tags=["Authentication"])

logger = logging.getLogger(__name__)

# ------------------------------------
# REGISTER
# ------------------------------------

@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    error: str | None = None
):
    return render(
        request,
        "auth/register.html",
        error=error
    )


@router.post("/register")
def register(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):

    hashed_password = pwd_context.hash(password)

    create_user(
        {
            "name": name,
            "username": username,
            "email": email,
            "password": hashed_password,
            "role": "user",
            "created_by": None,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": 1,
            "team_id": "cnk",
            "team_name": "CNK"
        }
    )

    return RedirectResponse(
        "/login?registered=1",
        status_code=303
    )


# ------------------------------------
# LOGIN
# ------------------------------------

@router.get("/login", response_class=HTMLResponse)
def login_page(
    request: Request,
    error: str | None = None,
    registered: bool = False
):

    return render(
        request,
        "auth/login.html",
        error=error,
        registered=registered,
    )


@router.post("/login")
def login(
    request: Request,
    login: str = Form(...),
    password: str = Form(...)
):
    user = get_user_by_login(login)
    if (
        not user
        or user["is_active"] != 1
        or not pwd_context.verify(password, user["password"])
    ):
        return RedirectResponse(
            "/login?error=Invalid username/email or password",
            status_code=303
        )
    request.session["user"] = {
        "id": user["id"],
        "name": user["name"],
        "username": user["username"],
        "email": user["email"],
        "role": user["role"],
        "team_id": user["team_id"],
        "team_name": user["team_name"]
    }
    request.session["last_activity"] = time.time()
    logger.info("User %s logged in", user["username"])
    return RedirectResponse("/", status_code=303)

# ------------------------------------
# LOGOUT
# ------------------------------------

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(
        "/login",
        status_code=303
    )
