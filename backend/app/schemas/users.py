from pydantic import BaseModel, EmailStr, ConfigDict

# Base Models
class UserBase(BaseModel):
    full_name: str
    email: EmailStr

# Authentication Requests
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str  # Plain text from frontend, Service layer will hash it

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# User Data Creation
class UserCreate(UserBase):
    password: str

# User Data Response
class UserResponse(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)