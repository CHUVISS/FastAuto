from __future__ import annotations

import json
import uuid

import pytest

from app.services.ai.ai_tools import (
    TOOLS_SCHEMA,
    execute_tool,
    validate_listing_id,
    validate_search_args,
)

pytestmark = pytest.mark.unit


def test_tools_schema_has_expected_tools():
    names = {tool["function"]["name"] for tool in TOOLS_SCHEMA}
    assert names == {"search_listings", "get_listing_details", "get_catalog_summary"}
    assert len(TOOLS_SCHEMA) == 3


def test_validate_search_args_strips_whitespace():
    cleaned = validate_search_args({"mark": "  Toyota  "})
    assert cleaned["mark"] == "Toyota"


def test_validate_search_args_drops_oversized_strings():
    long_mark = "x" * 101
    cleaned = validate_search_args({"mark": long_mark, "model": "Camry"})
    assert "mark" not in cleaned
    assert cleaned.get("model") == "Camry"


def test_validate_search_args_year_range_constraint():
    assert "year_from" not in validate_search_args({"year_from": 1899})
    assert "year_from" not in validate_search_args({"year_from": 2101})
    assert validate_search_args({"year_from": 2020})["year_from"] == 2020


def test_validate_search_args_negative_mileage_dropped():
    assert "max_mileage" not in validate_search_args({"max_mileage": -1})
    assert validate_search_args({"max_mileage": 50_000})["max_mileage"] == 50_000


def test_validate_search_args_negative_price_dropped():
    assert "max_price" not in validate_search_args({"max_price": -100})
    assert "min_price" not in validate_search_args({"min_price": -1})
    assert validate_search_args({"max_price": 5000})["max_price"] == 5000


def test_validate_listing_id_accepts_valid_uuid_string():
    listing_id = str(uuid.uuid4())
    assert validate_listing_id({"listing_id": listing_id}) == listing_id


def test_validate_listing_id_raises_for_non_string():
    with pytest.raises(ValueError, match="must be a string"):
        validate_listing_id({"listing_id": 12345})


def test_validate_listing_id_raises_for_invalid_uuid():
    with pytest.raises(ValueError, match="Invalid listing_id"):
        validate_listing_id({"listing_id": "not-a-uuid"})


async def test_execute_tool_returns_unknown_tool_error():
    result_json, error = await execute_tool("nonexistent_tool", {"foo": "bar"})
    assert error is not None
    assert "Unknown tool" in error
    payload = json.loads(result_json)
    assert "error" in payload
    assert "Unknown tool" in payload["error"]
