from datetime import timedelta, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from app.core.config import settings
from app.core.logger import logger
from app.core.redis_manager import redis_instance
from app.db.session import db
from app.models.user import User
from ...schemas.user_schemas import CreateUserRequest, Token

authLog = logger.get_context_logger("auth")

# Create an APIRouter
router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

# Initialize the password hashing context
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Create an OAuth2 Password Bearer for token authentication
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


# Database Dependency to get a database session
def get_db():
    """
    Get a database session.
    """
    db_instance = db.connect()
    try:
        yield db_instance
    finally:
        db_instance.close()


# Redis Dependency to get the Redis instance
def get_redis():
    """
    Get the Redis instance.
    """
    return redis_instance


# Database Dependency annotated for use in route functions
db_dependency = Annotated[Session, Depends(get_db)]


# Create a new user
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(pdb: db_dependency, create_user_request: CreateUserRequest):
    """
    Create a new user.

    Args:
        pdb (Session): Database session.
        create_user_request (CreateUserRequest): User data for creation.

    Returns:
        dict: User creation status.
    """
    try:
        create_user_model = User(
            username=create_user_request.username,
            password=bcrypt_context.hash(create_user_request.password),
            email=create_user_request.email,
            first_name=create_user_request.first_name,
            last_name=create_user_request.last_name,
        )
        pdb.add(create_user_model)
        pdb.commit()
        authLog.info(f"User created with id: {create_user_model.id}")
        return {"status": "User created successfully"}
    except IntegrityError as db_error:
        authLog.exception(db_error)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists"
        )
    except Exception as e:
        authLog.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Create an access token
def create_access_token(username: str, uuid: str, expires_delta: timedelta):
    """
    Create an access token.

    Args:
        username (str): User's username.
        uuid (str): User's UUID.
        expires_delta (timedelta): Token expiration duration.

    Returns:
        str: Access token.
    """
    encode = {"sub": username, "id": uuid}
    expires = datetime.utcnow() + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# Authenticate a user and issue tokens
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], database: db_dependency
):
    """
    Authenticate a user and issue tokens.

    Args:
        form_data (OAuth2PasswordRequestForm): OAuth2 form data with username and password.
        database (Session): Database session.

    Returns:
        Token: Access and refresh tokens.
    """
    try:
        user = authenticate_user(form_data.username, form_data.password, database)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        token = create_access_token(user.username, str(user.id), access_token_expires)
        refresh_token = create_access_token(
            user.username, str(user.id), refresh_token_expires
        )

        _store_token(token, str(user.id), access_token_expires, redis_instance)
        _store_refresh_token(
            refresh_token, str(user.id), refresh_token_expires, redis_instance
        )
        authLog.info(f"User {user.username} logged in")

        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as http_error:
        authLog.exception(http_error)
        raise http_error
    except JWTError as jwt_error:
        authLog.exception(jwt_error)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="JWT error"
        )
    except Exception as e:
        authLog.exception(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


# Authenticate a user
def authenticate_user(username: str, password: str, database) -> User | bool:
    """
    Authenticate a user.

    Args:
        username (str): User's username.
        password (str): User's password.
        database (Session): Database session.

    Returns:
        User | bool: Authenticated user or False.
    """
    try:
        user = database.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if not bcrypt_context.verify(password, user.password):
            return False
        return user
    except Exception as e:
        authLog.exception(e)
        return False


# Get the current user based on the token
async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """
    Get the current user based on the token.

    Args:
        token (str): Access token.

    Returns:
        dict: User information.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        user_id: str = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return {"username": username, "id": user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature has expired"
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )


# Store an access token in Redis
def _store_token(
    token: str, user_id: str, access_token_expires: timedelta, redis: redis_instance
):
    """
    Store an access token in Redis.

    Args:
        token (str): Access token.
        user_id (str): User's ID.
        access_token_expires (timedelta): Token expiration duration.
        redis (redis_instance): Redis instance.
    """
    try:
        redis_key = f"access_token:{user_id}"
        redis.set(redis_key, token, ex=access_token_expires)
        authLog.info(f"Access token stored for user {user_id}")
    except redis.exceptions.RedisError as redis_error:
        authLog.exception(redis_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error storing access token",
        )


# Store a refresh token in Redis
def _store_refresh_token(
    token: str, user_id: str, refresh_token_expires: timedelta, redis: redis_instance
):
    """
    Store a refresh token in Redis.

    Args:
        token (str): Refresh token.
        user_id (str): User's ID.
        refresh_token_expires (timedelta): Token expiration duration.
        redis (redis_instance): Redis instance.
    """
    try:
        redis_key = f"refresh_token:{user_id}"
        redis.set(redis_key, token, ex=refresh_token_expires)
        authLog.info(f"Refresh token stored for user {user_id}")
    except redis.exceptions.RedisError as redis_error:
        authLog.exception(redis_error)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error storing refresh token",
        )
