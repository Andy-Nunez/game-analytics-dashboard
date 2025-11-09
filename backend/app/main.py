from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app.routers import games

from .database import check_connection, get_db, Base, engine
from .import models, schemas
from .steam_client import fetch_steam_app_details, SteamAPIError

# Create all tables (runs at startup)
Base.metadata.create_all(bind=engine)

# Create the FastAPI app instance
app = FastAPI(
    title="Steam Games API",
    version="0.1.0",
)
# Register routers
app.include_router(games.router)

# --- ROUTES / ENDPOINTS ---

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/db-health")
def db_health():
    """
    Database connectivity check.
    """
    ok = check_connection()
    return {"database": "up" if ok else "down"}


@app.get("/", summary="Root endpoint")
def read_root():
    """Root route: health check or welcome message."""
    return {"message": "Welcome to the Game Analytics Dashboard API"}


# ------------ GAMES ENDPOINTS ------------

#Post requests


@app.post("/games", response_model=schemas.GameRead)
def create_game(game_in: schemas.GameCreate, db: Session = Depends(get_db)):
    """
    Create a new game in the database.
    """
    # Check if a game with same Steam appid already exists (optional)
    if game_in.steam_appid is not None:
        existing = (
            db.query(models.Game)
            .filter(models.Game.steam_appid == game_in.steam_appid)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail="A game with this Steam appid already exists.",
            )

    game = models.Game(
        name=game_in.name,
        steam_appid=game_in.steam_appid,
        genre=game_in.genre,
        developer=game_in.developer,
    )
    db.add(game)
    db.commit()
    db.refresh(game)  # reload from DB with id, timestamps
    return game

@app.post("/games/sync-steam/{steam_appid}", response_model=schemas.GameRead)
def sync_steam_game(steam_appid: int, db: Session = Depends(get_db)):
    """
    Fetch a game's data from the Steam Storefront API by appid,
    and upsert it into the local database.
    """
    game = sync_game_from_steam(steam_appid, db)
    return game

# Get requests

@app.get("/games", response_model=list[schemas.GameRead])
def list_games(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """
    List games in the database (paginated).
    """
    games = (
        db.query(models.Game)
        .order_by(models.Game.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return games


@app.get("/games/{game_id}", response_model=schemas.GameRead)
def get_game(game_id: int, db: Session = Depends(get_db)):
    """
    Get a single game by its ID.
    """
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game




@app.get("/games/sample")
def sample_game():
    """
    Temporary example endpoint — returns dummy game data.
    """
    return {
        "id": 1,
        "name": "Half-Life 2",
        "platform": "Steam",
        "genre": "Action",
        "developer": "Valve"
    }

# Helper function to sync game

def sync_game_from_steam(appid: int, db: Session) -> models.Game:
    """
    Fetch game info from Steam and upsert into the local database.

    - If a game with this steam_appid exists, update its fields.
    - Otherwise, create a new record.
    """
    try:
        steam_data = fetch_steam_app_details(appid)
    except SteamAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if not steam_data.get("name"):
        raise HTTPException(
            status_code=404,
            detail=f"No game name returned from Steam for appid {appid}.",
        )

    # Try to find an existing game with the same steam_appid
    game = (
        db.query(models.Game)
        .filter(models.Game.steam_appid == steam_data["steam_appid"])
        .first()
    )

    # Some simple normalizations
    genres = ", ".join(steam_data.get("genres") or [])
    developers = ", ".join(steam_data.get("developers") or [])

    if game:
        # Update existing
        game.name = steam_data["name"]
        game.genre = genres
        game.developer = developers
    else:
        # Create new
        game = models.Game(
            steam_appid=steam_data["steam_appid"],
            name=steam_data["name"],
            genre=genres,
            developer=developers,
        )
        db.add(game)

    db.commit()
    db.refresh(game)
    return game
