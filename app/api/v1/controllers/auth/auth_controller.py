from datetime import timedelta, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from app.core.logger import logger
from app.core.config import settings
from ...schemas.user_schemas import CreateUserRequest, Token
from app.db.session import db
from app.models.user import User

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
)

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')


def get_db():
    db_instance = db.connect()
    try:
        yield db_instance
    finally:
        db_instance.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(pdb: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = User(username=create_user_request.username,
                             password=bcrypt_context.hash(create_user_request.password),
                             email=create_user_request.email, first_name=create_user_request.first_name,
                             last_name=create_user_request.last_name)
    pdb.add(create_user_model)
    pdb.commit()
    logger.info(f"User created with id: {create_user_model.id}")


def create_access_token(username: str, uuid: str, expires_delta: timedelta):
    encode = {'sub': username, 'id': uuid}
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], database: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, database)
    logger.info(f"User {user.username} logged in")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(user.username, str(user.id), access_token_expires)
    return {'access_token': token, 'token_type': 'bearer'}


def authenticate_user(username: str, password: str, database) -> User | bool:
    user = database.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get('sub')
        user_id: str = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
        return {'username': username, 'id': user_id}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature has expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
