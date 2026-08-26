import logging
import os
import secrets
import time

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from routers import auth_router
from routers import dashboard_router
from routers import user_router
from routers import tender_router
from routers import manual_scraper_router
from dotenv  import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")


# =====================================================
# SESSION CONFIG
# =====================================================

SESSION_IDLE_TIMEOUT_SECONDS = 30 * 60  # 30 minutes
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60   # 8 hours

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    SESSION_SECRET_KEY = secrets.token_hex(32)
    logger.warning(
        "SESSION_SECRET_KEY is not set; using a randomly generated key "
        "for this process. Sessions will not persist across restarts. "
        "Set SESSION_SECRET_KEY in the environment for production use."
    )


# =====================================================
# SESSION TIMEOUT MIDDLEWARE
# =====================================================
class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if (
            request.url.path in ["/login", "/register", "/logout"]
            or request.url.path.startswith("/static")
            or request.url.path == "/favicon.ico"
        ):
            return await call_next(request)
        user = request.session.get("user")
        last_activity = request.session.get("last_activity")
        if user and last_activity:
            current_time = time.time()
            inactive_seconds = current_time - last_activity
            if inactive_seconds > SESSION_IDLE_TIMEOUT_SECONDS:
                logger.info("Session expired for user %s", user.get("username"))
                request.session.clear()
                return RedirectResponse(
                    url="/login?error=Session expired",
                    status_code=303
                )
            request.session["last_activity"] = current_time
        return await call_next(request)


# =====================================================
# CREATE FASTAPI APPLICATION
# =====================================================

app = FastAPI(
    title="FastAPI Application",
    version="1.0.0"
)


# =====================================================
# MIDDLEWARE
# =====================================================

# Add custom middleware first
app.add_middleware(
    SessionTimeoutMiddleware
)

# Add SessionMiddleware after it
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    max_age=SESSION_MAX_AGE_SECONDS
)


# =====================================================
# ROUTERS
# =====================================================
app.include_router(auth_router.router)
app.include_router(dashboard_router.router)
app.include_router(user_router.router)
app.include_router(tender_router.router)
app.include_router(manual_scraper_router.router)
