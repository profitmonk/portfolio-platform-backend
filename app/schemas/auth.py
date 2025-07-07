from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

# Request schemas (what users send to us)
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

# Response schemas (what we send back to users)
class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    display_name: Optional[str]
    is_active: bool
    public_profile: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
