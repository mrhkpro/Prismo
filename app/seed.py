from sqlalchemy.orm import Session

from . import config
from . import models
from . import security


def seed_admin(
    db: Session,
) -> None:

    """
    اگر هیچ کاربر ادمینی وجود نداشت،
    حساب ادمین پیش‌فرض را ایجاد می‌کند.
    """

    existing_admin = (
        db.query(models.User)
        .filter(
            models.User.role
            == models.UserRole.admin
        )
        .first()
    )

    if existing_admin:

        return

    admin = (
        db.query(models.User)
        .filter(
            models.User.username
            == config.ADMIN_USERNAME
        )
        .first()
    )

    if not admin:

        admin = models.User(
            username=config.ADMIN_USERNAME,

            org_name=config.ADMIN_ORG_NAME,

            password_hash=(
                security.hash_password(
                    config.ADMIN_PASSWORD
                )
            ),

            role=models.UserRole.admin,

            is_active=True,
        )

        db.add(admin)

        db.flush()

        db.add(
            models.UserSettings(
                user_id=admin.id,
                widget_title=config.ADMIN_ORG_NAME,
            )
        )

    else:

        admin.role = models.UserRole.admin

    db.commit()

    # Never print the admin password.
    print(
        "[seed] admin account ready -> "
        f"username={config.ADMIN_USERNAME}"
    )