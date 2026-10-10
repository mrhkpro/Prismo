from sqlalchemy import func
from sqlalchemy.orm import Session

from . import config
from . import models
from . import security


def seed_admin(db: Session) -> None:
    """Create or repair the configured bootstrap admin for local development.

    This function is called automatically for SQLite. It can also be explicitly
    enabled for a local development process connected to Supabase. The configured
    ADMIN_USERNAME and ADMIN_PASSWORD are authoritative for that bootstrap account.
    """
    username = config.ADMIN_USERNAME.strip()
    admin = (
        db.query(models.User)
        .filter(func.lower(models.User.username) == username.lower())
        .first()
    )

    if admin is not None:
        # Previous releases only promoted an existing user to admin but did not
        # update its password hash. That left the configured local admin password
        # unable to log in after an existing database was reused.
        admin.role = models.UserRole.admin
        admin.is_active = True
        if not security.verify_password(config.ADMIN_PASSWORD, admin.password_hash):
            admin.password_hash = security.hash_password(config.ADMIN_PASSWORD)

        if not admin.settings:
            db.add(
                models.UserSettings(
                    user_id=admin.id,
                    widget_title=config.ADMIN_ORG_NAME,
                )
            )
        if not admin.org_name:
            admin.org_name = config.ADMIN_ORG_NAME
        db.commit()
    else:
        # Avoid unexpectedly creating a second bootstrap administrator when the
        # local database is already initialized with a different admin account.
        existing_admin = (
            db.query(models.User)
            .filter(models.User.role == models.UserRole.admin)
            .first()
        )
        if existing_admin:
            return

        admin = models.User(
            username=username,
            org_name=config.ADMIN_ORG_NAME,
            password_hash=security.hash_password(config.ADMIN_PASSWORD),
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
        db.commit()

    # Never print credentials or password hashes.
    print(f"[seed] admin account ready -> username={username}")
