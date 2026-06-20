from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ReportRecommendation(BaseModel):
    category: str
    title: str
    description: str
    priority: str
    status: str = "Open"

class AuditReport(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    audit_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    email: Optional[str] = None
    website_url: str
    scan_type: str = "Full Audit"
    audit_score: int
    category_scores: Dict[str, float]
    recommendations: List[ReportRecommendation]
    issues_found: int = 0
    scan_status: str = "Completed"
    pdf_path: Optional[str] = None
    pdf_url: Optional[str] = None
    email_sent: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
