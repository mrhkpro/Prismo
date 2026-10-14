from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .. import models, schemas, i18n
from ..database import get_db
from ..security import get_current_user
from ..services import widget_extras, user_settings_compat

router = APIRouter(prefix="/api/widget", tags=["ویجت"])


@router.get("/config")
def get_widget_config(request: Request, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = user_settings_compat.get(db, current_user.id)
    language = i18n.get_language(request)
    extras, extras_available = widget_extras.load(db, current_user.id)
    return {
        "widget_id": s.widget_id,
        "widget_title": i18n.localize_widget_title(s.widget_title, language),
        "widget_welcome_message": i18n.localize_widget_welcome(s.widget_welcome_message, language),
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
    data = payload.model_dump(exclude_unset=True)
    if data.get("extras") is not None:
        widget_extras.sanitize(data["extras"])

    values = {
        key: data[key]
        for key in ("widget_title", "widget_welcome_message", "widget_color")
        if key in data and data[key]
    }
    if values:
        user_settings_compat.update_settings(db, current_user.id, values)
    db.commit()

    if data.get("extras") is not None:
        return {"ok": True, "extras": widget_extras.save(db, current_user.id, data["extras"])}
    return {"ok": True}


@router.get("/embed-code")
def get_embed_code(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = user_settings_compat.get(db, current_user.id)
    snippet = (
        f'<script\n'
        f'  src="__BASE_URL__/widget.js?v=2.8.8"\n'
        f'  data-widget-id="{s.widget_id}"\n'
        f'  data-api-base="__BASE_URL__"\n'
        f'  data-theme="auto"\n'
        f'  data-language="__LANGUAGE__"\n'
        f'  async>\n'
        f'</script>'
    )
    return {"widget_id": s.widget_id, "embed_code_template": snippet}
