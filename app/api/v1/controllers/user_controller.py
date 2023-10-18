from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from app.core.logger import logger
from .auth.auth_controller import get_current_user
from app.db.session import db
from app.models.user import User

router = APIRouter(
    prefix='/users',
    tags=['users'],
)


def get_db():
    db_instance = db.connect()
    try:
        yield db_instance
    finally:
        db_instance.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("/", status_code=HTTP_200_OK)
async def user(user: user_dependency, database: db_dependency):
    if user is None:
        logger.info("User not found")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return {"User": user}
