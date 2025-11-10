# backend/app/routers/games.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app import models, schemas
from app.database import SessionLocal

router = APIRouter(
    prefix="/games",
    tags=["Games"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependency to get a DB session per request
@router.get("/{game_id}", response_model=schemas.Game)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game

@router.get("/", response_model=List[schemas.Game])
def list_games(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    games = db.query(models.Game).offset(skip).limit(limit).all()
    return games


@router.post("/", response_model=schemas.Game)
def create_game(
    game_in: schemas.GameCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new game row in the DB from the validated input schema.
    Note: For now we only persist a subset of fields that exist on the Game model.
    """
    db_game = models.Game(
        name=game_in.name,
        source="steam",                                # hard-coded for now
        source_game_id=game_in.steam_appid,           # map steam_appid -> source_game_id
        genre=game_in.genre,
        # other fields (platform, hours_played, price_usd, rating, completed)
        # will use their default values defined on the SQLAlchemy model
    )

    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game
