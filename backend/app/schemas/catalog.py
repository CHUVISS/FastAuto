from typing import Any, TypedDict


class MarkDict(TypedDict):
    id: str
    name: str | None
    cyrillic_name: str | None
    numeric_id: int | None
    year_from: int | None
    year_to: int | None
    popular: bool | None
    country: str | None
    updated_at: str | None


ModelDict = TypedDict(
    "ModelDict",
    {
        "id": str,
        "mark_id": str | None,
        "name": str | None,
        "cyrillic_name": str | None,
        "year_from": int | None,
        "year_to": int | None,
        "class": str | None,
        "updated_at": str | None,
    },
)


class GenerationDict(TypedDict):
    id: str
    model_id: str | None
    mark_id: str | None
    name: str | None
    year_from: int | None
    year_to: int | None
    updated_at: str | None


class ConfigurationDict(TypedDict):
    id: str
    generation_id: str | None
    model_id: str | None
    mark_id: str | None
    name: str | None
    body_type: str | None
    doors_count: int | None
    updated_at: str | None


class ModificationDict(TypedDict):
    id: str
    configuration_id: str | None
    generation_id: str | None
    model_id: str | None
    mark_id: str | None
    name: str | None
    group_name: str | None
    offers_price_from: int | None
    offers_price_to: int | None
    is_closed: bool | None
    updated_at: str | None


class ModificationFullDict(TypedDict):
    modification: ModificationDict
    generation: GenerationDict | None
    configuration: ConfigurationDict | None
    specification: dict[str, Any] | None
    options: dict[str, Any] | None


class ColorDict(TypedDict):
    id: str
    name_ru: str
    name_en: str | None
    hex_code: str | None
    sort_order: int
