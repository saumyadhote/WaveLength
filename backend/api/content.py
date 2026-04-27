from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.core.config import get_settings
from backend.core.security import get_current_user_id
from backend.models.content import TMDBSearchResult

router = APIRouter(prefix="/content", tags=["content"])

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def _parse_tmdb_result(
    item: dict, media_type: Literal["movie", "tv"]
) -> TMDBSearchResult:
    """Map a raw TMDB search hit to our typed model."""
    title = item.get("title") or item.get("name") or "Unknown"
    release_date = item.get("release_date") or item.get("first_air_date")
    return TMDBSearchResult(
        tmdb_id=item["id"],
        title=title,
        media_type=media_type,
        overview=item.get("overview") or None,
        poster_path=item.get("poster_path"),
        release_date=release_date or None,
        genre_ids=item.get("genre_ids", []),
    )


@router.get("/search", response_model=list[TMDBSearchResult])
async def search_content(
    query: str = Query(min_length=1, description="Search term"),
    media_type: Literal["movie", "tv"] = Query(default="movie", alias="type", description="Media type"),
    page: int = Query(default=1, ge=1, le=500),
    _user_id: str = Depends(get_current_user_id),
) -> list[TMDBSearchResult]:
    """
    Search movies or TV shows via TMDB.
    Requires a valid JWT in the Authorization header.
    """
    settings = get_settings()
    endpoint = f"{TMDB_BASE_URL}/search/{media_type}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            endpoint,
            params={
                "api_key": settings.tmdb_api_key,
                "query": query,
                "page": page,
                "include_adult": False,
            },
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch results from TMDB.",
        )

    data = response.json()
    results = data.get("results", [])

    return [_parse_tmdb_result(item, media_type) for item in results]
