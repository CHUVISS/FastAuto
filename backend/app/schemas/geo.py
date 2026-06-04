from typing import TypedDict


class RegionDict(TypedDict):
    id: str
    code: str
    iso_code: str
    name_ru: str
    fullname_ru: str
    name_en: str | None
    type_: str
    district: str | None


class CityDict(TypedDict):
    id: str
    region_id: str
    name_ru: str
    name_en: str | None
    type_: str
    latitude: float | None
    longitude: float | None
    timezone: str | None
    is_capital: bool
    is_popular: bool


class CitiesGrouped(TypedDict):
    popular: list[CityDict]
    all: list[CityDict]
