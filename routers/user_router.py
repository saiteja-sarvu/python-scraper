import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import JSONResponse

from database import get_db
from utils.auth import require_login
from utils.security import pwd_context
from utils.template import render

from model.user_model import (
    update_user as update_user_model,
    get_user_by_id,
    create_user as create_user_model
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_login)]
)

logger = logging.getLogger(__name__)


@router.get("")
async def users(request: Request):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM ai_users
                ORDER BY id DESC
            """)
            users = cursor.fetchall()
    finally:
        conn.close()
    return render(
        request,
        "users/index.html",
        users=users
    )


@router.get("/list")
async def get_all_users():
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *
                FROM ai_users
                ORDER BY id DESC
            """)
            users = cursor.fetchall()
    finally:
        conn.close()
    return JSONResponse(content=users)

@router.get("/add")
async def add_user(request: Request):
    return render(request, "users/add.html")

@router.post("/add")
async def create_user(
    request: Request,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    team_id: str = Form(...),
    team_name: str = Form(...)
):

    hashed_password = pwd_context.hash(password)
    data = {
        "name": name,
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": role,
        "created_by": None,
        "created_at": datetime.now(),
        "is_active": 1,
        "team_id": team_id,
        "team_name": team_name
    }
    user_id = create_user_model(data)
    return {
        "success": True,
        "message": "User created successfully",
        "user_id": user_id,
        "redirect": "/users"
    }


@router.get("/edit/{user_id}")
async def edit_user(
    request: Request,
    user_id: int
):
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return render(
        request,
        "users/edit.html",
        user=user
    )

@router.post("/update/{user_id}")
async def update_user(
    user_id: int,
    name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    role: str = Form(...),
    team_id: str = Form(...),
    team_name: str = Form(...),
    is_active: int = Form(...),
    password: str = Form("")
):
    logger.info("Updating user %s", user_id)
    data = {
        "name": name,
        "username": username,
        "email": email,
        "role": role,
        "team_id": team_id,
        "team_name": team_name,
        "is_active": is_active
    }
    if password:
        hashed_password = pwd_context.hash(password)
        data["password"] = hashed_password
    else:
        data["password"] = None
    affected_rows = update_user_model(user_id, data)
    if affected_rows == 0:
        return {
            "success": True,
            "message": "No changes were made."
        }
    return {
        "success": True,
        "message": "User updated successfully"
    }
