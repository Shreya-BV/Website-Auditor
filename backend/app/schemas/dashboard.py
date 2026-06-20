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
    recent_leads: List[Lead]
    recent_visitors: List[VisitorLog]
    scans_by_day: List[DailyCount]
    leads_by_day: List[DailyCount]
