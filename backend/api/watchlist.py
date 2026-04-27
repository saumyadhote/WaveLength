from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.database import get_db
from backend.core.security import get_current_user_id
from backend.models.content import (
    LogContentRequest,
    WatchedContentInDB,
    WatchedContentPublic,
)

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def _to_public(doc: dict) -> WatchedContentPublic:
    """Convert a raw MongoDB document to the public response model."""
    return WatchedContentPublic(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        tmdb_id=doc["tmdb_id"],
        title=doc["title"],
        media_type=doc["media_type"],
        poster_path=doc.get("poster_path"),
        genres=doc.get("genres", []),
        overview=doc.get("overview"),
        user_rating=doc.get("user_rating"),
        user_notes=doc.get("user_notes"),
        emotional_tags=doc.get("emotional_tags", []),
        watched_at=doc["watched_at"],
    )


@router.post("/log", response_model=WatchedContentPublic, status_code=status.HTTP_201_CREATED)
async def log_content(
    body: LogContentRequest,
    user_id: str = Depends(get_current_user_id),
) -> WatchedContentPublic:
    """
    Add a movie or TV show to the current user's watchlist.
    Prevents duplicate entries for the same TMDB ID.
    """
    db = get_db()

    existing = await db.watched_content.find_one(
        {"user_id": user_id, "tmdb_id": body.tmdb_id}
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already logged this title.",
        )

    watched_at = body.watched_at or datetime.now(timezone.utc)

    entry = WatchedContentInDB(
        user_id=user_id,
        tmdb_id=body.tmdb_id,
        title=body.title,
        media_type=body.media_type,
        poster_path=body.poster_path,
        genres=body.genres,
        overview=body.overview,
        user_rating=body.user_rating,
        user_notes=body.user_notes,
        emotional_tags=body.emotional_tags,
        watched_at=watched_at,
    )

    await db.watched_content.insert_one(entry.model_dump(by_alias=True))
    return _to_public(entry.model_dump(by_alias=True))


@router.get("/me", response_model=list[WatchedContentPublic])
async def get_my_watchlist(
    user_id: str = Depends(get_current_user_id),
) -> list[WatchedContentPublic]:
    """Return all logged content for the authenticated user, newest first."""
    db = get_db()
    cursor = db.watched_content.find(
        {"user_id": user_id}
    ).sort("watched_at", -1)

    docs = await cursor.to_list(length=200)
    return [_to_public(doc) for doc in docs]


@router.get("/me/{entry_id}", response_model=WatchedContentPublic)
async def get_watchlist_entry(
    entry_id: str,
    user_id: str = Depends(get_current_user_id),
) -> WatchedContentPublic:
    """Return a single watchlist entry by its ID. Only accessible by the owner."""
    db = get_db()
    doc = await db.watched_content.find_one(
        {"_id": entry_id, "user_id": user_id}
    )

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found.",
        )

    return _to_public(doc)
