from fastapi import APIRouter, HTTPException, status

from backend.core.database import get_db
from backend.core.security import create_access_token, hash_password, verify_password
from backend.models.user import AuthResponse, LoginRequest, RegisterRequest, UserInDB

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest) -> AuthResponse:
    """
    Create a new user account.
    Returns a JWT so the client is immediately logged in after registering.
    """
    db = get_db()

    # Reject duplicate email or username
    existing = await db.users.find_one(
        {"$or": [{"email": body.email}, {"username": body.username}]}
    )
    if existing:
        field = "email" if existing.get("email") == body.email else "username"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with that {field} already exists.",
        )

    user = UserInDB(
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
    )

    await db.users.insert_one(user.model_dump(by_alias=True))

    token = create_access_token(subject=user.id)
    return AuthResponse(access_token=token, user_id=user.id, username=user.username)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest) -> AuthResponse:
    """
    Authenticate with email + password.
    Returns a JWT on success.
    """
    db = get_db()

    doc = await db.users.find_one({"email": body.email})

    # Use a generic message to avoid leaking whether the email exists
    if not doc or not verify_password(body.password, doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = create_access_token(subject=str(doc["_id"]))
    return AuthResponse(
        access_token=token,
        user_id=str(doc["_id"]),
        username=doc["username"],
    )
