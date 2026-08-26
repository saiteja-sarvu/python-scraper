import os
import logging
import time
import hashlib
import secrets
from datetime import datetime, timedelta
from utils.email import send_password_reset_email
from fastapi import APIRouter, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse

from model.user_model import (
    create_user,
    get_user_by_login,
    get_user_by_email,
    create_password_reset_token,
    get_password_reset_token,
    mark_password_reset_token_used,
    update_password
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
    registered: bool = False,
    password_reset: bool = False
):

    return render(
        request,
        "auth/login.html",
        error=error,
        registered=registered,
        password_reset=password_reset
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
# FORGOT PASSWORD
# ------------------------------------

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(
    request: Request,
    error: str | None = None,
    success: str | None = None
):
    return render(
        request,
        "auth/forgot_password.html",
        error=error,
        success=success
    )

def _issue_password_reset(user):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()
    expires_at = datetime.now() + timedelta(minutes=30)
    create_password_reset_token(
        user["id"],
        token_hash,
        expires_at,
        datetime.now()
    )

    base_url = os.getenv(
        "APP_BASE_URL",
        "http://127.0.0.1:8000"
    )
    reset_url = (
        f"{base_url}/reset-password"
        f"?token={token}"
    )
    email_sent = send_password_reset_email(
        recipient_email=user["email"],
        recipient_name=user["name"],
        reset_url=reset_url
    )
    if not email_sent:
        logger.error(
            "Password reset email could not be sent to %s",
            user["email"]
        )


@router.post("/forgot-password")
def forgot_password(
    request: Request,
    background_tasks: BackgroundTasks,
    email: str = Form(...)
):
    user = get_user_by_email(email)
    if user:
        background_tasks.add_task(_issue_password_reset, user)

    return RedirectResponse(
        "/forgot-password?success=1",
        status_code=303
    )

# ------------------------------------
# RESET PASSWORD
# ------------------------------------

@router.get("/reset-password", response_class=HTMLResponse)
def reset_password_page(
    request: Request,
    token: str
):
    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    reset_token = get_password_reset_token(token_hash)

    if not reset_token:
        return render(
            request,
            "auth/reset_password.html",
            error="This password reset link is invalid or has expired.",
            token=None
        )

    return render(
        request,
        "auth/reset_password.html",
        error=None,
        token=token
    )


@router.post("/reset-password")
def reset_password(
    request: Request,
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    if password != confirm_password:
        return render(
            request,
            "auth/reset_password.html",
            error="Passwords do not match.",
            token=token
        )

    if len(password) < 8:
        return render(
            request,
            "auth/reset_password.html",
            error="Password must be at least 8 characters.",
            token=token
        )

    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    reset_token = get_password_reset_token(token_hash)

    if not reset_token:
        return render(
            request,
            "auth/reset_password.html",
            error="This password reset link is invalid or has expired.",
            token=None
        )

    hashed_password = pwd_context.hash(password)

    update_password(
        reset_token["user_id"],
        hashed_password
    )

    mark_password_reset_token_used(
        reset_token["id"]
    )

    return RedirectResponse(
        "/login?password_reset=1",
        status_code=303
    )
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
