from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..security import get_current_user
from ..services import widget_extras

router = APIRouter(prefix="/api/widget", tags=["ویجت"])


@router.get("/config")
def get_widget_config(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = current_user.settings
    extras, extras_available = widget_extras.load(db, current_user.id)
    return {
        "widget_id": s.widget_id,
        "widget_title": s.widget_title,
        "widget_welcome_message": s.widget_welcome_message,
        "widget_color": s.widget_color,
        "extras": extras,
        "extras_available": extras_available,
    }


@router.put("/config")
def update_widget_config(
    payload: schemas.WidgetConfigUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    s = current_user.settings
    data = payload.model_dump(exclude_unset=True)
    if "widget_title" in data and data["widget_title"]:
        s.widget_title = data["widget_title"]
    if "widget_welcome_message" in data and data["widget_welcome_message"]:
        s.widget_welcome_message = data["widget_welcome_message"]
    if "widget_color" in data and data["widget_color"]:
        s.widget_color = data["widget_color"]
    if data.get("extras") is not None:
        # اعتبارسنجی پیش از هر نوشتن، تا ورودی نامعتبر نیمه‌کاره ذخیره نشود
        widget_extras.sanitize(data["extras"])
    db.commit()
    if data.get("extras") is not None:
        return {"ok": True, "extras": widget_extras.save(db, current_user.id, data["extras"])}
    return {"ok": True}


@router.get("/embed-code")
def get_embed_code(current_user: models.User = Depends(get_current_user)):
    s = current_user.settings
    snippet = (
        f'<script\n'
        f'  src="__BASE_URL__/widget.js?v=2.4.0"\n'
        f'  data-widget-id="{s.widget_id}"\n'
        f'  data-api-base="__BASE_URL__"\n'
        f'  data-theme="auto"\n'
        f'  async>\n'
        f'</script>'
    )
    return {"widget_id": s.widget_id, "embed_code_template": snippet}
