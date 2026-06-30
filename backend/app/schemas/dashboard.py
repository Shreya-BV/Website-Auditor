from pydantic import BaseModel
from typing import List
from .lead import Lead
from .visitor import VisitorLog

class DailyCount(BaseModel):
    date: str
    count: int

class DashboardStats(BaseModel):
    total_visitors: int
    total_scans: int
    total_leads: int
    average_score: float = 0
    total_audits: int = 0
    visitors_today: int = 0
    leads_today: int = 0
    conversion_rate: float = 0
    average_scan_time_ms: float = 0
    most_common_issue: str = "N/A"
    most_missing_feature: str = "N/A"
    top_performing_website: str = "N/A"
    recent_leads: List[Lead] = []
    recent_visitors: List[VisitorLog] = []
    scans_by_day: List[DailyCount] = []
    leads_by_day: List[DailyCount] = []
