from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ScanRequest(BaseModel):
    url: str

class Recommendation(BaseModel):
    pillar: str
    item: str
    recommendation: str
    issue: Optional[str] = None
    reason: Optional[str] = None
    business_impact: Optional[str] = None
    how_to_fix: Optional[str] = None
    estimated_time: Optional[str] = None
    priority: Optional[str] = None
    expected_score_increase: Optional[int] = None

class CheckResult(BaseModel):
    found: bool
    confidence: int
    method: str

class MeasurementChecks(BaseModel):
    google_analytics: CheckResult
    gtm: CheckResult
    clarity: CheckResult
    hotjar: CheckResult

class RetargetingChecks(BaseModel):
    meta_pixel: CheckResult
    google_ads: CheckResult
    linkedin_insight: CheckResult

class ConversionChecks(BaseModel):
    contact_form: CheckResult
    whatsapp: CheckResult
    live_chat: CheckResult
    crm: CheckResult
    lead_popup: CheckResult

class TrustChecks(BaseModel):
    https: CheckResult
    ssl: CheckResult
    privacy_policy: CheckResult
    terms: CheckResult
    contact_page: CheckResult

class SeoAiChecks(BaseModel):
    meta_title: CheckResult
    meta_description: CheckResult
    sitemap: CheckResult
    robots: CheckResult
    schema_markup: CheckResult
    opengraph: CheckResult
    twitter_card: CheckResult
    llms_txt: CheckResult

class PillarChecks(BaseModel):
    measurement: MeasurementChecks
    retargeting: RetargetingChecks
    conversion: ConversionChecks
    trust: TrustChecks
    seo_ai: SeoAiChecks

class PillarScores(BaseModel):
    measurement: float
    retargeting: float
    conversion: float
    trust: float
    seo_ai: float

class AuditReportResponse(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    url: str
    overall_score: int
    grade: str
    pillar_scores: PillarScores
    checks: PillarChecks
    recommendations: List[Recommendation]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
