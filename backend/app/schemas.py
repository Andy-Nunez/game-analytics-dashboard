from datetime import datetime
from pydantic import BaseModel


class GameBase(BaseModel):
    name: str
    steam_appid: int | None = None
    genre: str | None = None
    developer: str | None = None


class GameCreate(GameBase):
    """
    Data required to create a new game.
    For now it's the same as GameBase.
    """
    pass


class GameRead(GameBase):
    """
    Data returned to the client when reading a game.
    """
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True  # <- important so Pydantic can read from ORM objects
