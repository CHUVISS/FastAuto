import uuid

from pydantic import BaseModel


class FavoriteIn(BaseModel):
    listing_id: uuid.UUID
