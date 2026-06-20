from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class LeadCreate(BaseModel):
    name: str
    email: str
    website_url: str
    audit_score: int

class Lead(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    email: str
    website_url: str
    audit_score: int
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
