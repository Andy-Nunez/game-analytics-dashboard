from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    steam_appid = Column(Integer, unique=True, index=True, nullable=True)
    name = Column(String, index=True, nullable=False)
    genre = Column(String, nullable=True)
    developer = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

