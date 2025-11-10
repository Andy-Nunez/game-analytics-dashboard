from .database import Base
from datetime import datetime, date

from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Numeric
from sqlalchemy.sql import func
from sqlalchemy.sql.sqltypes import DateTime

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)

    # Steam-specific identifier
    steam_appid = Column(Integer, index=True, unique=True, nullable=True)

    # Core metadata
    name = Column(String, index=True, nullable=False)
    genre = Column(String, index=True, nullable=True)
    developer = Column(String, nullable=True)
    publisher = Column(String, nullable=True)

    release_date = Column(Date, nullable=True)
    is_free = Column(Boolean, default=False)
    metacritic_score = Column(Integer, nullable=True)
    recommendations_count = Column(Integer, nullable=True)

    header_image = Column(String, nullable=True)
    languages = Column(String, nullable=True)
    categories = Column(String, nullable=True)

    # You can keep analytics-ish fields for later if you want:
    platform = Column(String, default="PC")
    hours_played = Column(Integer, default=0)
    price_usd = Column(Numeric(10, 2), nullable=True)
    rating = Column(Float, nullable=True)
    completed = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


