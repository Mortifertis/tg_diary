from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
VERSIONS_DIR = MIGRATIONS_DIR / "versions"
INITIAL_REVISION = "0001_initial_schema"


@pytest.fixture()
def alembic_config(tmp_path: Path) -> Config:
    db_file = tmp_path / "migration_smoke.db"
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("script_location", str(MIGRATIONS_DIR))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_file}")
    return config


def test_migrations_upgrade_and_downgrade_smoke(alembic_config: Config) -> None:
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")


def test_migrations_have_single_head(alembic_config: Config) -> None:
    script = ScriptDirectory.from_config(alembic_config)
    heads = script.get_heads()
    assert len(heads) == 1, (
        "Expected one migration head to avoid merge conflicts. "
        f"Current heads: {heads}"
    )


def _extract_table_from_call(call_line: str) -> str | None:
    normalized = call_line.strip().replace('"', "'")
    markers = (
        "op.add_column('",
        "op.drop_column('",
        "op.create_index('",
        "op.drop_index('",
        "op.create_table('",
        "op.drop_table('",
    )
    for marker in markers:
        if marker not in normalized:
            continue
        tail = normalized.split(marker, maxsplit=1)[1]
        parts = tail.split("',")
        if len(parts) < 2:
            continue
        if "index" in marker:
            return parts[1].strip().strip("')")
        return parts[0]
    return None


def _tables_touched_in_upgrade(file_content: str) -> set[str]:
    in_upgrade = False
    touched: set[str] = set()
    for raw_line in file_content.splitlines():
        line = raw_line.strip()
        if line.startswith("def upgrade"):
            in_upgrade = True
            continue
        if in_upgrade and line.startswith("def downgrade"):
            break
        if not in_upgrade:
            continue
        table = _extract_table_from_call(line)
        if table:
            touched.add(table)
    return touched


def test_each_revision_has_single_responsibility() -> None:
    for revision_file in sorted(VERSIONS_DIR.glob("*.py")):
        if revision_file.name.startswith("__"):
            continue
        content = revision_file.read_text(encoding="utf-8")
        if f'revision = "{INITIAL_REVISION}"' in content:
            continue
        touched_tables = _tables_touched_in_upgrade(content)
        assert touched_tables, (
            f"No schema operations found in {revision_file.name}."
        )
        assert len(touched_tables) == 1, (
            "Each migration must change one responsibility "
            "(single table/object scope). "
            f"{revision_file.name} touches: {sorted(touched_tables)}"
        )
