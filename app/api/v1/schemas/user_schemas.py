from pydantic import BaseModel, Field, EmailStr


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=4, max_length=20, description="Username must be 4-20 characters.")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters.")
    email: EmailStr = Field(..., description="Please provide a valid email address.")
    first_name: str = Field(..., description="First name is required.")
    last_name: str = Field(..., description="Last name is required.")


class Token(BaseModel):
    access_token: str
    token_type: str
