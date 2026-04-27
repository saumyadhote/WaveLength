from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field
from bson import ObjectId


# ── DB document shape ─────────────────────────────────────────────────────────

class WatchedContentInDB(BaseModel):
    """Represents a watched-content entry stored in MongoDB."""
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: str

    # TMDB-sourced fields
    tmdb_id: int
    title: str
    media_type: Literal["movie", "tv"]
    poster_path: str | None = None
    genres: list[str] = []
    overview: str | None = None

    # User-provided fields
    user_rating: int | None = Field(default=None, ge=1, le=10)
    user_notes: str | None = None
    emotional_tags: list[str] = []

    watched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


# ── Request / response shapes ─────────────────────────────────────────────────

class LogContentRequest(BaseModel):
    tmdb_id: int
    title: str
    media_type: Literal["movie", "tv"]
    poster_path: str | None = None
    genres: list[str] = []
    overview: str | None = None
    user_rating: int | None = Field(default=None, ge=1, le=10)
    user_notes: str | None = None
    emotional_tags: list[str] = []
    watched_at: datetime | None = None


class WatchedContentPublic(BaseModel):
    """Safe shape returned to the client."""
    id: str
    user_id: str
    tmdb_id: int
    title: str
    media_type: Literal["movie", "tv"]
    poster_path: str | None
    genres: list[str]
    overview: str | None
    user_rating: int | None
    user_notes: str | None
    emotional_tags: list[str]
    watched_at: datetime


# ── TMDB search result shape ──────────────────────────────────────────────────

class TMDBSearchResult(BaseModel):
    tmdb_id: int
    title: str
    media_type: Literal["movie", "tv"]
    overview: str | None
    poster_path: str | None
    release_date: str | None  # "2010-07-16" or None
    genre_ids: list[int]
