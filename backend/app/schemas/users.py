from typing import Literal

from pydantic import BaseModel, EmailStr, ConfigDict, Field

# Base Models
class UserBase(BaseModel):
    full_name: str
    email: EmailStr

# Authentication Requests
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str  # Plain text from frontend, Service layer will hash it
    role: Literal["user", "admin", "administrator"] = "user"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Literal["user", "admin", "administrator"] = "user"

# User Data Creation
class UserCreate(UserBase):
    password: str

# User Data Response
class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    role: Literal["user", "admin", "administrator"] = "user"

    model_config = ConfigDict(from_attributes=True)


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=6)
    note: str | None = None
