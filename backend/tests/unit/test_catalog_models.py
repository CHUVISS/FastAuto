import pytest

from app.models.catalog import (
    Configuration,
    Generation,
    Mark,
    Model,
    Modification,
    Options,
    Specification,
)

pytestmark = pytest.mark.unit

_ALL = (Mark, Model, Generation, Configuration, Modification, Specification, Options)


def test_catalog_tables_in_catalog_schema():
    for model in _ALL:
        assert model.__table__.schema == "catalog"


def test_mark_columns():
    names = {c.name for c in Mark.__table__.columns}
    assert {"id", "name", "cyrillic_name", "popular", "country"} <= names


def test_model_maps_class_column():
    names = {c.name for c in Model.__table__.columns}
    assert "class" in names


def test_modification_fk_columns():
    names = {c.name for c in Modification.__table__.columns}
    assert {"id", "mark_id", "model_id", "generation_id", "configuration_id"} <= names


def test_specification_has_engine_type():
    names = {c.name for c in Specification.__table__.columns}
    assert {"id", "displacement", "power", "engine_type"} <= names


def test_options_digit_prefixed_columns_present():
    names = {c.name for c in Options.__table__.columns}
    assert {"12v_socket", "360_camera", "abs"} <= names


def test_options_public_dict_uses_real_db_names():
    opts = Options(id="X")
    pub = opts.to_public_dict()
    assert "360_camera" in pub
    assert "12v_socket" in pub
    assert "abs" in pub
    assert pub["id"] == "X"
