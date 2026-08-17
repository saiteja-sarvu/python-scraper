from datetime import date
from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


def render(request: Request, template_name: str, **context):
    data = {
        "request": request,
        "user": request.session.get("user"),
        "current_year": date.today().year,
    }

    data.update(context)

    return templates.TemplateResponse(
        request,
        template_name,
        data
    )