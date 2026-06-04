from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class GeoRegion(SQLModel, table=True):
    __tablename__ = "regions"
    __table_args__ = {"schema": "geo"}

    id: str = Field(primary_key=True, max_length=13)
    code: str = Field(max_length=10, unique=True)
    iso_code: str = Field(max_length=10, unique=True)
    name_ru: str = Field(max_length=100)
    fullname_ru: str = Field(max_length=200)
    name_en: str | None = Field(default=None, max_length=100)
    type_: str = Field(max_length=50)
    district: str | None = Field(default=None, max_length=50)
    okato: str | None = Field(default=None, max_length=20)
    population: int | None = None


class GeoCity(SQLModel, table=True):
    __tablename__ = "cities"
    __table_args__ = (
        Index("idx_cities_region", "region_id"),
        Index(
            "idx_cities_name_trgm",
            "name_ru",
            postgresql_using="gin",
            postgresql_ops={"name_ru": "gin_trgm_ops"},
        ),
        Index("idx_cities_popular", "is_popular"),
        {"schema": "geo"},
    )

    id: str = Field(primary_key=True, max_length=13)
    region_id: str = Field(foreign_key="geo.regions.id", max_length=13)
    name_ru: str = Field(max_length=100)
    name_en: str | None = Field(default=None, max_length=100)
    type_: str = Field(max_length=50)
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = Field(default=None, max_length=50)
    population: int | None = None
    is_capital: bool = Field(default=False)
    is_popular: bool = Field(default=False)
    okato: str | None = Field(default=None, max_length=20)
    zip_code: str | None = Field(default=None, max_length=10)
