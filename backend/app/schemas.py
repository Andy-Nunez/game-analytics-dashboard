from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


class GameBase(BaseModel):
    name: str
    steam_appid: Optional[int] = None

    genre: Optional[str] = None
    developer: Optional[str] = None
    publisher: Optional[str] = None

    release_date: Optional[date] = None
    is_free: bool = False
    metacritic_score: Optional[int] = None
    recommendations_count: Optional[int] = None

    header_image: Optional[str] = None
    languages: Optional[str] = None
    categories: Optional[str] = None


class GameCreate(GameBase):
    """
    Data the client sends when creating a game manually.
    For now, same as GameBase.
    """
    pass


class GameRead(GameBase):
    """
    Data returned to the client when reading a game.
    Matches the SQLAlchemy Game model.
    """
    id: int
    created_at: datetime
    updated_at: datetime

class Game(GameBase):
    id: int
    created_at: datetime
    updated_at: datetime

class Config:
    # Pydantic v2 way to say "you can create me from ORM objects"
    from_attributes = True
