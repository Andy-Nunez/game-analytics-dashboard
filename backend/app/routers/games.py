from fastapi import APIRouter
from typing import List

router = APIRouter(
    prefix="/games",       # All routes here will start with /games
    tags=["Games"]         # Used in the docs UI
)

# Example in-memory dataset
games_data = [
    {"id": 1, "name": "Elden Ring", "platform": "PC"},
    {"id": 2, "name": "Hades", "platform": "PC"},
]

@router.get("/", summary="List all games")
def list_games() -> List[dict]:
    """Return a list of games (mock data for now)."""
    return games_data
