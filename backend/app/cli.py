"""Small maintenance CLI: ``python -m app.cli <command>``."""

from __future__ import annotations

import sys

from app.core.config import settings
from app.db.session import SessionLocal, init_db
from app.services.maintenance import purge_old_logs

COMMANDS = ("init-db", "purge-logs")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(f"usage: python -m app.cli [{' | '.join(COMMANDS)}]")
        return 1

    command = args[0]
    if command == "init-db":
        init_db()
        print(f"Schema created in {settings.database_url}")
        return 0

    with SessionLocal() as db:
        deleted = purge_old_logs(db)
    print(f"Deleted {deleted} request logs older than {settings.log_retention_days} days")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
