from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

log = logging.getLogger("import_catalog")

_RESERVED = {
    "class",
    "default",
    "order",
    "group",
    "user",
    "table",
    "column",
    "select",
    "where",
    "primary",
    "key",
    "references",
    "check",
    "constraint",
    "from",
    "to",
    "all",
    "case",
    "end",
    "limit",
    "offset",
}

_TABLE_LOAD_ORDER = [
    "marks",
    "models",
    "generations",
    "configurations",
    "body_types_dic",
    "specifications_dic",
    "options_dic",
    "modifications",
    "specifications",
    "options",
    "specifications_raw",
]

_APP_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_modifications_mark_model "
    "ON catalog.modifications (mark_id, model_id)",
    "CREATE INDEX IF NOT EXISTS idx_configurations_body_type "
    "ON catalog.configurations (body_type)",
    "CREATE INDEX IF NOT EXISTS idx_specifications_engine_type "
    "ON catalog.specifications (engine_type)",
    "CREATE INDEX IF NOT EXISTS idx_catalog_models_mark ON catalog.models (mark_id)",
    "CREATE INDEX IF NOT EXISTS idx_catalog_generations_model "
    "ON catalog.generations (model_id)",
    "CREATE INDEX IF NOT EXISTS idx_catalog_configurations_generation "
    "ON catalog.configurations (generation_id)",
]

_DROP_LINE = re.compile(
    r"^(UNIQUE\s+KEY|KEY|CONSTRAINT|FOREIGN\s+KEY|UNIQUE\b)", re.IGNORECASE
)
_PRIMARY_LINE = re.compile(r"^PRIMARY\s+KEY", re.IGNORECASE)


def _quote_ident(name: str) -> str:
    if re.fullmatch(r"[a-z_][a-z0-9_]*", name) and name not in _RESERVED:
        return name
    return f'"{name}"'


def _replace_backticked(text: str) -> str:
    return re.sub(r"`([^`]+)`", lambda m: _quote_ident(m.group(1)), text)


def _convert_types(line: str) -> str:
    is_bool = re.search(r"\btinyint\(1\)", line, re.IGNORECASE) is not None
    line = re.sub(r"\btinyint\(1\)", "boolean", line, flags=re.IGNORECASE)
    line = re.sub(r"\bbigint\(\d+\)", "bigint", line, flags=re.IGNORECASE)
    line = re.sub(r"\bmediumint\(\d+\)", "integer", line, flags=re.IGNORECASE)
    line = re.sub(r"\bint\(\d+\)", "integer", line, flags=re.IGNORECASE)
    line = re.sub(r"\bsmallint\(\d+\)", "smallint", line, flags=re.IGNORECASE)
    line = re.sub(r"\btinyint\(\d+\)", "smallint", line, flags=re.IGNORECASE)
    line = re.sub(r"\s+unsigned\b", "", line, flags=re.IGNORECASE)
    line = re.sub(r"\s+CHARACTER SET \w+", "", line, flags=re.IGNORECASE)
    line = re.sub(r"\s+COLLATE \w+", "", line, flags=re.IGNORECASE)
    line = re.sub(r"\s+ON UPDATE current_timestamp\(\)", "", line, flags=re.IGNORECASE)
    line = re.sub(
        r"current_timestamp\(\)", "CURRENT_TIMESTAMP", line, flags=re.IGNORECASE
    )
    if is_bool:
        line = re.sub(r"\bDEFAULT 0\b", "DEFAULT false", line)
        line = re.sub(r"\bDEFAULT 1\b", "DEFAULT true", line)
    return line


def mysql_ddl_to_pg(sql: str, schema: str) -> str:
    sql = sql.strip().rstrip(";").strip()
    name_match = re.search(r"CREATE TABLE\s+`?([^`\s(]+)`?", sql, re.IGNORECASE)
    if not name_match:
        return sql
    table = name_match.group(1)
    body = sql[sql.index("(") + 1 : sql.rindex(")")]

    kept: list[str] = []
    for raw in body.splitlines():
        line = raw.strip().rstrip(",").strip()
        if not line:
            continue
        if _DROP_LINE.match(line):
            continue
        if _PRIMARY_LINE.match(line):
            kept.append(_replace_backticked(line))
            continue
        kept.append(_convert_types(_replace_backticked(line)))

    inner = ",\n  ".join(kept)
    return f"CREATE TABLE IF NOT EXISTS {schema}.{_quote_ident(table)} (\n  {inner}\n);"


def insert_to_pg(sql: str, schema: str) -> str:
    sql = _replace_backticked(sql.strip())
    return re.sub(
        r"INSERT INTO\s+([a-z_][a-z0-9_]*)",
        rf"INSERT INTO {schema}.\1",
        sql,
        count=1,
        flags=re.IGNORECASE,
    )


def _boolean_columns(ddl: str) -> list[str]:
    cols: list[str] = []
    for line in ddl.splitlines():
        m = re.match(
            r'\s*(?:"([^"]+)"|([a-z_][a-z0-9_]*))\s+boolean\b', line, re.IGNORECASE
        )
        if m:
            cols.append(m.group(1) or m.group(2))
    return cols


def _to_staging_ddl(ddl: str) -> str:
    ddl = re.sub(r"\bDEFAULT true\b", "DEFAULT 1", ddl)
    ddl = re.sub(r"\bDEFAULT false\b", "DEFAULT 0", ddl)
    return re.sub(r"\bboolean\b", "smallint", ddl)


def _alter_to_boolean(schema: str, table: str, cols: list[str]) -> str:
    actions = []
    for col in cols:
        ident = _quote_ident(col)
        actions.append(f"ALTER COLUMN {ident} DROP DEFAULT")
        actions.append(
            f"ALTER COLUMN {ident} TYPE boolean USING ({ident}::int::boolean)"
        )
    return f"ALTER TABLE {schema}.{_quote_ident(table)} " + ", ".join(actions)


def _iter_statements(dump: str):
    table_re = re.compile(
        r"CREATE TABLE.*?\)\s*ENGINE=[^;]*;", re.IGNORECASE | re.DOTALL
    )
    for m in table_re.finditer(dump):
        yield "create", m.group(0)
    insert_re = re.compile(
        r"^INSERT INTO .*?;\s*$", re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    for m in insert_re.finditer(dump):
        yield "insert", m.group(0)


def load_cars_catalog(dump_path: Path, schema: str = "catalog") -> int:
    """Re-create catalog.* tables and load them from a MariaDB dump.

    Returns the number of tables loaded.
    """
    from app.core.db import sync_engine

    dump = dump_path.read_text(encoding="utf-8", errors="replace")
    creates: dict[str, str] = {}
    inserts: dict[str, list[str]] = {}
    for kind, stmt in _iter_statements(dump):
        if kind == "create":
            name = re.search(r"CREATE TABLE\s+`?([^`\s(]+)`?", stmt, re.IGNORECASE)
            if name:
                creates[name.group(1)] = mysql_ddl_to_pg(stmt, schema)
        else:
            name = re.search(r"INSERT INTO\s+`?([^`\s(]+)`?", stmt, re.IGNORECASE)
            if name:
                inserts.setdefault(name.group(1), []).append(insert_to_pg(stmt, schema))

    bool_cols = {t: _boolean_columns(ddl) for t, ddl in creates.items()}
    loaded = 0

    def _raw(conn, statement: str) -> None:
        conn.exec_driver_sql(statement.replace("%", "%%"))

    with sync_engine.begin() as conn:
        _raw(conn, f"CREATE SCHEMA IF NOT EXISTS {schema}")
        _raw(conn, "SET standard_conforming_strings = off")
        for table in reversed(_TABLE_LOAD_ORDER):
            if table in creates:
                _raw(
                    conn,
                    f"DROP TABLE IF EXISTS {schema}.{_quote_ident(table)} CASCADE",
                )
        for table in _TABLE_LOAD_ORDER:
            if table in creates:
                _raw(conn, _to_staging_ddl(creates[table]))
                loaded += 1
        for table in _TABLE_LOAD_ORDER:
            for stmt in inserts.get(table, []):
                _raw(conn, stmt)
        for table in _TABLE_LOAD_ORDER:
            if bool_cols.get(table):
                _raw(conn, _alter_to_boolean(schema, table, bool_cols[table]))
        for index_sql in _APP_INDEXES:
            _raw(conn, index_sql)
    return loaded


def main(argv: list[str] | None = None) -> int:
    from app.core.config import settings
    from app.core.log import configure_logging

    configure_logging(settings)

    argv = argv if argv is not None else sys.argv[1:]
    default = Path(__file__).resolve().parent.parent / "data" / "carsbase2_dump.sql"
    dump_path = Path(argv[0]) if argv else default
    if not dump_path.exists():
        log.error("dump not found: %s", dump_path)
        return 1
    log.warning(
        "scripts.import_catalog is the low-level loader; prefer "
        "`python -m scripts.seed_catalog --source cars` for hash-based delta seeding"
    )
    n = load_cars_catalog(dump_path)
    log.info("catalog imported from %s (%d tables)", dump_path, n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
