from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class ScanRequest(BaseModel):
    url: str

class Recommendation(BaseModel):
    pillar: str
    item: str
    recommendation: str

class MeasurementChecks(BaseModel):
    google_analytics: bool
    gtm: bool
    clarity: bool
    hotjar: bool

class RetargetingChecks(BaseModel):
    meta_pixel: bool
    google_ads: bool
    linkedin_insight: bool

class ConversionChecks(BaseModel):
    contact_form: bool
    whatsapp: bool
    live_chat: bool
    crm: bool
    lead_popup: bool

class TrustChecks(BaseModel):
    https: bool
    ssl: bool
    privacy_policy: bool
    terms: bool
    contact_page: bool

class SeoAiChecks(BaseModel):
    meta_title: bool
    meta_description: bool
    sitemap: bool
    robots: bool
    schema_markup: bool
    opengraph: bool
    twitter_card: bool
    llms_txt: bool

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
