from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from dateutil import parser as date_parser  # pip install python-dateutil (already done earlier)

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

# CORS middleware (adjust origins as needed)

# Allow frontend dev server to call the API

origins = [
    "http://localhost:5173",  # Vite default
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to sync game

def sync_game_from_steam(appid: int, db: Session) -> models.Game:
    try:
        steam_data = fetch_steam_app_details(appid)
    except SteamAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    if not steam_data.get("name"):
        raise HTTPException(
            status_code=404,
            detail=f"No game name returned from Steam for appid {appid}.",
        )

    genres = ", ".join(steam_data.get("genres") or [])
    developers = ", ".join(steam_data.get("developers") or [])
    publishers = ", ".join(steam_data.get("publishers") or [])
    categories = ", ".join(steam_data.get("categories") or [])

    release_date_str = steam_data.get("release_date")
    release_date = None
    if release_date_str:
        try:
            release_date = date_parser.parse(release_date_str).date()
        except Exception:
            release_date = None

    game = (
        db.query(models.Game)
        .filter(models.Game.steam_appid == steam_data["steam_appid"])
        .first()
    )

    if game:
        game.name = steam_data["name"]
        game.genre = genres
        game.developer = developers
        game.publisher = publishers
        game.release_date = release_date
        game.is_free = steam_data.get("is_free", False)
        game.metacritic_score = steam_data.get("metacritic_score")
        game.recommendations_count = steam_data.get("recommendations_count")
        game.header_image = steam_data.get("header_image")
        game.languages = steam_data.get("languages")
        game.categories = categories
    else:
        game = models.Game(
            steam_appid=steam_data["steam_appid"],
            name=steam_data["name"],
            genre=genres,
            developer=developers,
            publisher=publishers,
            release_date=release_date,
            is_free=steam_data.get("is_free", False),
            metacritic_score=steam_data.get("metacritic_score"),
            recommendations_count=steam_data.get("recommendations_count"),
            header_image=steam_data.get("header_image"),
            languages=steam_data.get("languages"),
            categories=categories,
        )
        db.add(game)

    db.commit()
    db.refresh(game)
    return game



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


@app.post("/games/sync-steam-batch")
def sync_steam_batch(
    appids: list[int] = Body(..., example=[620, 570, 730]),
    db: Session = Depends(get_db),
):
    """
    Batch-sync multiple Steam appids.

    Body: [620, 570, 730, ...]
    Returns a list of results showing success or error per appid.
    """
    results = []
    for appid in appids:
        try:
            game = sync_game_from_steam(appid, db)
            results.append({
                "appid": appid,
                "ok": True,
                "id": game.id,
                "name": game.name,
            })
        except HTTPException as exc:
            results.append({
                "appid": appid,
                "ok": False,
                "error": exc.detail,
            })
        except Exception as exc:
            results.append({
                "appid": appid,
                "ok": False,
                "error": str(exc),
            })
    return results

