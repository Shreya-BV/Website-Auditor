from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="Password must be between 6 and 128 characters")

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    operating_system: Optional[str] = None
    device_type: Optional[str] = None
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    remember_me: Optional[bool] = False

class UserResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    login_count: int
    status: str

    class Config:
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
