from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class VisitorCreate(BaseModel):
    browser: str
    device: str
    referrer: str
    page_visited: str

class VisitorLog(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    ip_address: str
    browser: str
    device: str
    referrer: str
    page_visited: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
