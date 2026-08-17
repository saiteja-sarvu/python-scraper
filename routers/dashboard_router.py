from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from utils.auth import require_login
from utils.template import render

router = APIRouter(dependencies=[Depends(require_login)])


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return render(request, "dashboard/index.html")
