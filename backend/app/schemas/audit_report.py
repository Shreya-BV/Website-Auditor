from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ReportRecommendation(BaseModel):
    category: str
    title: str
    description: str
    priority: str  # Critical, High, Medium, Low
    status: str = "Open"
    current_problem: Optional[str] = None
    business_impact: Optional[str] = None
    technical_explanation: Optional[str] = None
    implementation_steps: Optional[str] = None
    estimated_time: Optional[str] = None
    expected_score_improvement: Optional[int] = None
    difficulty: Optional[str] = None
    evidence: Optional[str] = None

class PerformanceMetrics(BaseModel):
    response_time_ms: Optional[float] = None
    rendering_time_ms: Optional[float] = None
    html_download_time_ms: Optional[float] = None
    playwright_time_ms: Optional[float] = None
    detection_time_ms: Optional[float] = None
    total_scan_time_ms: Optional[float] = None
    rendering_method: Optional[str] = None # "HTTPX" or "Playwright"

class TechnologyDetection(BaseModel):
    name: str
    found: bool
    evidence: Optional[str] = None
    confidence: Optional[int] = None

class PillarDetail(BaseModel):
    score: float
    passed_checks: int
    failed_checks: int
    confidence: int
    business_explanation: str
    technical_explanation: str

class AuditReport(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    audit_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    email: Optional[str] = None
    website_url: str
    website_title: Optional[str] = None
    scan_type: str = "Full Audit"
    audit_score: int
    grade: Optional[str] = None
    benchmark: str = "Average"
    target_score: str = "85+"
    category_scores: Dict[str, float]
    pillar_details: Optional[Dict[str, PillarDetail]] = None
    recommendations: List[ReportRecommendation]
    checks: Optional[Dict[str, Any]] = None
    issues_found: int = 0
    technology_detections: Optional[List[TechnologyDetection]] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    scan_status: str = "Completed"
    pdf_path: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_generated: bool = False
    pdf_gridfs_id: Optional[str] = None
    pdf_filename: Optional[str] = None
    email_sent: bool = False
    email_sent_at: Optional[datetime] = None
    delivery_status: str = "Pending"
    error_message: Optional[str] = None
    download_count: int = 0
    last_downloaded: Optional[datetime] = None
    view_count: int = 0
    last_viewed: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
