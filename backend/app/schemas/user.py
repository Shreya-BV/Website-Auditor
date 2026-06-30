from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters long")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    full_name: str
    email: str
    created_date: datetime
    last_login: Optional[datetime] = None
    login_count: int
    account_status: str

    class Config:
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
