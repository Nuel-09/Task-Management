from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from bson import ObjectId

from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.database import get_db
from app.models.user import USERS_COLLECTION, build_user_document, serialize_user
from app.schemas.user import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def _auth_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
    except ValueError as exc:
        raise _auth_exception() from exc

    if not user_id or not ObjectId.is_valid(user_id):
        raise _auth_exception()

    user = await db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise _auth_exception()

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    existing_user = await db[USERS_COLLECTION].find_one({"email": payload.email.lower()})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address already registered",
        )

    document = build_user_document(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
    )
    result = await db[USERS_COLLECTION].insert_one(document)
    created_user = await db[USERS_COLLECTION].find_one({"_id": result.inserted_id})
    return serialize_user(created_user)


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: UserLoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
) -> dict:
    user = await db[USERS_COLLECTION].find_one({"email": payload.email.lower()})
    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=str(user["_id"]))
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/logout")
async def logout_user() -> dict:
    # Stateless JWT auth: logout is handled client-side by dropping the token.
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: dict = Depends(get_current_user)) -> dict:
    return serialize_user(current_user)
