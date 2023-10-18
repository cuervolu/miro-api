from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    is_staff: bool = False
    first_name: str = None
    last_name: str = None
