from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LoginHistory(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    email: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    browser: Optional[str] = None
    browser_version: Optional[str] = None
    operating_system: Optional[str] = None
    device_type: Optional[str] = None
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    country: Optional[str] = None
    referrer: Optional[str] = None
    remember_me_enabled: bool = False
    login_status: str = "Success"

    class Config:
        populate_by_name = True
