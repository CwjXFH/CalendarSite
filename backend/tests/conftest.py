import atexit
import os
import tempfile
from pathlib import Path


def pytest_configure() -> None:
    fd, name = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DB_PATH"] = name
    os.environ.setdefault("OPS_TOKEN", "test-ops-token")
    from app.db.database import require_db
    from app.services.holiday import bootstrap_holidays_if_empty

    require_db()
    bootstrap_holidays_if_empty()
    atexit.register(lambda: Path(name).unlink(missing_ok=True))
