from uuid import uuid4

from sqlalchemy import Column, String, Boolean, UUID

from app.db.base_class import Base


class User(Base):
    id = Column(UUID, primary_key=True, index=True, default=uuid4)
    username = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_staff = Column(Boolean, nullable=False, default=False)
