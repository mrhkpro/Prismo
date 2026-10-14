from contextlib import asynccontextmanager

import logging
import time
import uuid

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
)

from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    JSONResponse,
)

from fastapi.staticfiles import (
    StaticFiles,
)

from . import config, i18n

from .database import (
    Base,
    SessionLocal,
    engine,
)

from .exceptions import (
    AppError,
)

from .seed import (
    seed_admin,
)

from .services import user_settings_compat

from .routers import (
    admin,
    auth,
    dashboard,
    knowledge,
    playground,
    public_widget,
    settings,
    widget,
)


# ============================================================
# LIFESPAN
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Fast startup lifecycle.

    Supabase/Postgres is treated as an already-initialized database: the app does
    not run create_all, schema inspection, ALTER TABLE, or seed queries on boot.
    This removes the network round-trips that previously made local+Supabase startup
    appear frozen. SQLite keeps its local-only bootstrap/migration behavior.
    """
    if not config.IS_POSTGRES:
        Base.metadata.create_all(bind=engine)

        # Local SQLite databases created before 2.7 need the new provider columns.
        with engine.begin() as connection:
            columns = {col["name"] for col in inspect(connection).get_columns("user_settings")}
            if "separate_embedding_provider" not in columns:
                connection.execute(text("ALTER TABLE user_settings ADD COLUMN separate_embedding_provider BOOLEAN NOT NULL DEFAULT 0"))
            if "embedding_api_key" not in columns:
                connection.execute(text("ALTER TABLE user_settings ADD COLUMN embedding_api_key VARCHAR(255)"))
            if "embedding_base_url" not in columns:
                connection.execute(text("ALTER TABLE user_settings ADD COLUMN embedding_base_url VARCHAR(255)"))
            if "embedding_use_default_provider" not in columns:
                connection.execute(text("ALTER TABLE user_settings ADD COLUMN embedding_use_default_provider BOOLEAN"))
                connection.execute(text("UPDATE user_settings SET embedding_use_default_provider = use_default_provider WHERE embedding_use_default_provider IS NULL"))

        # Only local SQLite needs the bootstrap admin on every fresh project.
        db = SessionLocal()
        try:
            seed_admin(db)
        finally:
            db.close()
    elif config.IS_POSTGRES and not config.IS_VERCEL:
        # Local + Supabase: repair only additive settings columns before any
        # request can trigger a full ORM UserSettings SELECT. Vercel keeps its
        # explicit migration flow and does not run DDL at startup.
        added_columns = user_settings_compat.ensure_local_supabase_provider_schema(engine)
        if added_columns:
            logging.getLogger("prismo").warning(
                "Local+Supabase compatibility added user_settings columns: %s",
                ", ".join(added_columns),
            )
        if config.APP_ENV == "development" and config.BOOTSTRAP_ADMIN_ON_STARTUP:
            db = SessionLocal()
            try:
                seed_admin(db)
            finally:
                db.close()
    elif config.APP_ENV == "development" and config.BOOTSTRAP_ADMIN_ON_STARTUP:
        # Preserve optional bootstrap behavior for development previews.
        db = SessionLocal()
        try:
            seed_admin(db)
        finally:
            db.close()

    yield


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title=config.APP_TITLE,
    lifespan=lifespan,
)


@app.get("/api/runtime")
def runtime_info():
    return {
        "database_mode": config.DATABASE_MODE,
        "database": "supabase" if config.IS_POSTGRES else "local",
        "vercel": config.IS_VERCEL,
        "local_session_stable": not config.IS_VERCEL,
    }


# ============================================================
# LOGGING
# ============================================================

logger = logging.getLogger(
    "prismo"
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.WARNING),
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)


# ============================================================
# REQUEST LOGGING
# ============================================================

@app.middleware("http")
async def database_error_middleware(request: Request, call_next):
    """Fail fast and localize unreachable PostgreSQL/Supabase connections."""
    try:
        return await call_next(request)
    except OperationalError:
        language = i18n.get_language(request)
        detail = i18n.localize_message("پایگاه‌داده موقتاً در دسترس نیست.", language)
        return JSONResponse(
            status_code=503,
            content={"detail": detail},
            headers={"Cache-Control": "no-store"},
        )


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):

    request_id = uuid.uuid4().hex

    request.state.request_id = (
        request_id
    )

    started = time.perf_counter()

    try:

        response = await call_next(
            request
        )

        elapsed_ms = int(
            (
                time.perf_counter()
                - started
            )
            * 1000
        )

        response.headers[
            "X-Request-ID"
        ] = request_id

        # فایل‌های استاتیکِ نسخه‌دار (/assets/...?v=...) را مرورگر و CDN می‌توانند بلندمدت کش کنند.
        # با هر انتشار، شماره‌ی ?v= در صفحه‌ها عوض می‌شود. ‏HTML و widget.js عمداً کش بلندمدت نمی‌گیرند.
        # محتوای گفت‌وگو/ویجت عمومی نباید توسط مرورگر، CDN یا موتور جست‌وجو cache/index شود.
        no_store_path = (
            request.url.path.startswith("/public/widget/")
            or request.url.path in {
                "/", "/index.html", "/dashboard.html", "/admin.html",
                "/setup.html", "/widget.js", "/widget-preview.html",
            }
            or request.url.path.endswith(".html")
        )
        if no_store_path:
            response.headers["Cache-Control"] = "no-store, no-cache, no-transform, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-Robots-Tag"] = "noindex, noarchive, nosnippet"

        if (
            request.method == "GET"
            and request.url.path.startswith("/assets/")
            and "v" in request.query_params
            and response.status_code == 200
        ):
            response.headers[
                "Cache-Control"
            ] = "public, max-age=31536000, immutable"

        # Do not log every static asset/request by default. Logging is opt-in
        # or automatically enabled for slow requests, which keeps local startup
        # and busy dashboards quiet.
        if config.REQUEST_LOGGING or elapsed_ms >= config.SLOW_REQUEST_MS:
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id, request.method, request.url.path, response.status_code, elapsed_ms,
            )

        return response

    except Exception:

        elapsed_ms = int(
            (
                time.perf_counter()
                - started
            )
            * 1000
        )

        logger.exception(
            "request_id=%s "
            "method=%s "
            "path=%s "
            "duration_ms=%s",

            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )

        raise


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=False,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(
    auth.router
)

app.include_router(
    dashboard.router
)

app.include_router(
    settings.router
)

app.include_router(
    knowledge.router
)

app.include_router(
    playground.router
)

app.include_router(
    widget.router
)

app.include_router(
    public_widget.router
)

app.include_router(
    admin.router
)


# ============================================================
# APPLICATION ERROR HANDLER
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    language = i18n.get_language(request)
    detail = exc.detail
    if isinstance(detail, str):
        detail = i18n.localize_message(detail, language)
    elif isinstance(detail, list):
        detail = [
            i18n.localize_message(item, language) if isinstance(item, str) else item
            for item in detail
        ]
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=dict(exc.headers or {}),
    )


@app.exception_handler(
    AppError
)
async def app_error_handler(
    request: Request,
    exc: AppError,
):

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": i18n.localize_message(str(exc), i18n.get_language(request))
        },
    )


# ============================================================
# GENERIC ERROR HANDLER
# ============================================================

@app.exception_handler(
    Exception
)
async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
):

    request_id = getattr(
        request.state,
        "request_id",
        None,
    )

    logger.exception(
        "Unhandled exception request_id=%s",
        request_id,
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": i18n.localize_message("سرویس موقتاً در دسترس نیست.", i18n.get_language(request)),
            "request_id": request_id,
        },
        headers=(
            {
                "X-Request-ID": request_id
            }
            if request_id
            else None
        ),
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/api/health")
def health():

    return {
        "status": "ok"
    }


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/",
    StaticFiles(
        directory=config.FRONTEND_DIR,
        html=True,
    ),
    name="frontend",
)