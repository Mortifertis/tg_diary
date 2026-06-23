from __future__ import annotations

from dotenv import load_dotenv

from app.config import load_config
from app.db import run_migrations


def main() -> None:
    load_dotenv()
    config = load_config()
    run_migrations(config.database_url)


if __name__ == "__main__":
    main()
