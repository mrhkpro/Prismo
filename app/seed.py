from sqlalchemy import func
from sqlalchemy.orm import Session

from . import config
from . import models
from . import security
from .services import user_settings_compat


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

        # Do not touch ``admin.settings`` here. Loading that SQLAlchemy
        # relationship selects every mapped UserSettings column, which can
        # crash development+Supabase startup when an older hosted schema is
        # missing optional provider columns. The compatibility service selects
        # only columns that actually exist and creates a narrow legacy row when
        # needed.
        user_settings_compat.ensure_settings(
            db, admin.id, widget_title=config.ADMIN_ORG_NAME
        )
        if not admin.org_name:
            admin.org_name = config.ADMIN_ORG_NAME
        db.commit()
    else:
        # The configured bootstrap identity is authoritative for local development.
        # If it is missing, create it even if another admin account exists; otherwise
        # a fresh/reconfigured local installation could never use ADMIN_USERNAME.
        admin = models.User(
            username=username,
            org_name=config.ADMIN_ORG_NAME,
            password_hash=security.hash_password(config.ADMIN_PASSWORD),
            role=models.UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.flush()
        user_settings_compat.ensure_settings(
            db, admin.id, widget_title=config.ADMIN_ORG_NAME
        )
        db.commit()

    # Never print credentials or password hashes.
    print(f"[seed] admin account ready -> username={username}")
