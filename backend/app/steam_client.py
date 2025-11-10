import requests


class SteamAPIError(Exception):
    """Custom exception for Steam API issues."""
    pass


def fetch_steam_app_details(appid: int) -> dict:
    """
    Fetch game details from the Steam Storefront API.

    Returns a dict like:
    {
        "steam_appid": 620,
        "name": "Portal 2",
        "genres": ["Action", "Adventure"],
        "developers": ["Valve"]
    }
    """
    url = "https://store.steampowered.com/api/appdetails"
    params = {"appids": appid}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise SteamAPIError(f"Network error calling Steam API: {exc}") from exc

    data = resp.json()

    # The API returns { "<appid>": { "success": bool, "data": { ... } } }
    app_key = str(appid)
    if app_key not in data or not data[app_key].get("success"):
        raise SteamAPIError(f"Steam API did not return data for appid {appid}.")

    app_data = data[app_key].get("data", {})

    # Normalize a bit
    name = app_data.get("name")
    genres_data = app_data.get("genres", []) or []
    developers_data = app_data.get("developers", []) or []

    genres_data = app_data.get("genres", []) or []
    developers_data = app_data.get("developers", []) or []
    publishers_data = app_data.get("publishers", []) or []
    categories_data = app_data.get("categories", []) or []

    genres = [g.get("description") for g in genres_data if isinstance(g, dict)]
    developers = [d for d in developers_data if isinstance(d, str)]
    publishers = [p for p in publishers_data if isinstance(p, str)]
    categories = [c.get("description") for c in categories_data if isinstance(c, dict)]

    release_date = app_data.get("release_date") or {}
    release_date_str = release_date.get("date")  # e.g. "Apr 18, 2011"

    metacritic = app_data.get("metacritic") or {}
    metacritic_score = metacritic.get("score")

    recommendations = app_data.get("recommendations") or {}
    rec_count = recommendations.get("total")

    supported_languages = app_data.get("supported_languages")  # usually HTML-ish string
    header_image = app_data.get("header_image")
    is_free = bool(app_data.get("is_free", False))

    return {
        "steam_appid": app_data.get("steam_appid"),
        "name": name,

        "genres": genres,
        "developers": developers,
        "publishers": publishers,
        "categories": categories,

        "release_date": release_date_str,
        "is_free": is_free,
        "metacritic_score": metacritic_score,
        "recommendations_count": rec_count,

        "header_image": header_image,
        "languages": supported_languages,
    }
