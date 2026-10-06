"""محیط تست را از SDK شبکه‌ای OpenAI مستقل می‌کند."""
import os
import sys
import types

os.environ["APP_ENV"] = "development"
os.environ["DATABASE_URL"] = "sqlite://"


if "openai" not in sys.modules:
    fake_openai = types.ModuleType("openai")

    class OpenAI:  # noqa: N801
        pass

    class APIError(Exception):
        pass

    class APIConnectionError(APIError):
        pass

    class AuthenticationError(APIError):
        pass

    fake_openai.OpenAI = OpenAI
    fake_openai.APIError = APIError
    fake_openai.APIConnectionError = APIConnectionError
    fake_openai.AuthenticationError = AuthenticationError
    sys.modules["openai"] = fake_openai


# محیط تست ممکن است بدون پکیج اختیاری pgvector اجرا شود؛ این shim فقط برای تست
# ساخت کوئری PostgreSQL است و در runtime واقعی، pgvector از requirements نصب می‌شود.
if "pgvector.sqlalchemy" not in sys.modules:
    try:
        import importlib.util
        _pgvector_available = importlib.util.find_spec("pgvector.sqlalchemy") is not None
    except Exception:
        _pgvector_available = False
    if not _pgvector_available:
        from sqlalchemy import Text
        from sqlalchemy.types import TypeDecorator, UserDefinedType

        class _VectorComparator(UserDefinedType.Comparator):
            def cosine_distance(self, other):
                return self.expr.op("<=>")(other)

        class VECTOR(TypeDecorator):
            impl = Text
            cache_ok = True
            comparator_factory = _VectorComparator

            def __init__(self, dim=None, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.dim = dim

        pgvector_module = types.ModuleType("pgvector")
        pgvector_sqlalchemy = types.ModuleType("pgvector.sqlalchemy")
        pgvector_sqlalchemy.VECTOR = VECTOR
        pgvector_module.sqlalchemy = pgvector_sqlalchemy
        sys.modules["pgvector"] = pgvector_module
        sys.modules["pgvector.sqlalchemy"] = pgvector_sqlalchemy
