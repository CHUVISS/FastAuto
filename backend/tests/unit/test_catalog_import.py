import pytest

from scripts.import_catalog import mysql_ddl_to_pg

pytestmark = pytest.mark.unit


def test_strips_backticks_and_engine():
    src = (
        "CREATE TABLE `marks` (\n"
        "  `id` varchar(50) NOT NULL,\n"
        "  PRIMARY KEY (`id`)\n"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;"
    )
    out = mysql_ddl_to_pg(src, schema="catalog")
    assert "`" not in out
    assert "ENGINE=" not in out
    assert "COLLATE" not in out
    assert "CREATE TABLE IF NOT EXISTS catalog.marks" in out


def test_tinyint1_becomes_boolean():
    src = "CREATE TABLE `options` (\n  `abs` tinyint(1) DEFAULT 0\n) ENGINE=InnoDB;"
    out = mysql_ddl_to_pg(src, schema="catalog")
    assert "boolean" in out.lower()
    assert "tinyint" not in out.lower()


def test_on_update_current_timestamp_removed():
    src = (
        "CREATE TABLE `marks` (\n"
        "  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() "
        "ON UPDATE current_timestamp()\n"
        ") ENGINE=InnoDB;"
    )
    out = mysql_ddl_to_pg(src, schema="catalog")
    assert "ON UPDATE" not in out
    assert "current_timestamp()" not in out
    assert "CURRENT_TIMESTAMP" in out


def test_int_widths_stripped():
    src = (
        "CREATE TABLE `models` (\n"
        "  `numeric_id` bigint(20) DEFAULT NULL,\n"
        "  `year_from` smallint(6) DEFAULT NULL\n"
        ") ENGINE=InnoDB;"
    )
    out = mysql_ddl_to_pg(src, schema="catalog")
    assert "bigint(20)" not in out
    assert "smallint(6)" not in out
    assert "bigint" in out
    assert "smallint" in out


def test_inline_key_lines_dropped():
    src = (
        "CREATE TABLE `marks` (\n"
        "  `id` varchar(50) NOT NULL,\n"
        "  `updated_at` timestamp NULL,\n"
        "  PRIMARY KEY (`id`),\n"
        "  KEY `marks_updated_at_index` (`updated_at`)\n"
        ") ENGINE=InnoDB;"
    )
    out = mysql_ddl_to_pg(src, schema="catalog")
    assert "KEY `marks_updated_at_index`" not in out
    assert "marks_updated_at_index" not in out
    assert "PRIMARY KEY (id)" in out


def test_class_column_quoted_as_reserved_word():
    src = (
        "CREATE TABLE `models` (\n  `class` varchar(10) DEFAULT NULL\n) ENGINE=InnoDB;"
    )
    out = mysql_ddl_to_pg(src, schema="catalog")
    assert '"class"' in out
