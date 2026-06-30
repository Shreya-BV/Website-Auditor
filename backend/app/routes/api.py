from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

from app.database.mongodb import get_database
from app.schemas.scan import ScanRequest, AuditReportResponse
from app.schemas.visitor import VisitorCreate, VisitorLog
from app.schemas.lead import LeadCreate, Lead
from app.schemas.dashboard import DashboardStats, DailyCount
from app.scanners.engine import run_scan
from app.routes.audit import process_audit_workflow
from app.routes.auth import get_current_user

router = APIRouter()

def serialize_doc(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

def serialize_list(docs):
    return [serialize_doc(doc) for doc in docs]

import traceback

@router.post("/scan", response_model=AuditReportResponse)
async def scan_website(payload: ScanRequest, db=Depends(get_database)):
    current_user = {"_id": "test_id", "full_name": "Test User"}
    print("Scan request received")
    print("Website URL:", payload.url)
    logger.info(f"Received scan request for URL: {payload.url}")
    if not payload.url or len(payload.url.strip()) == 0:
        raise HTTPException(status_code=400, detail="Invalid website URL.")
    
    url = payload.url.strip()
    # Basic URL cleaning
    if not url.startswith("http://") and not url.startswith("https://"):
        # We check if it looks like a domain. If it doesn't contain a dot, throw error.
        if "." not in url:
            raise HTTPException(status_code=400, detail="Please enter a valid website domain.")
    
    try:
        print("Starting scraper")
        logger.info(f"Starting backend processing for {url}")
        # Run scanning engine
        report = await run_scan(url)
        logger.info(f"Scan completed for {url}. Score: {report.get('overall_score')}")
        # Store in database (legacy)
        result = await db["scans"].insert_one(report)
        report["_id"] = str(result.inserted_id)
        
        # New Audit Report System mapping
        mapped_recs = []
        for r in report.get("recommendations", []):
            mapped_recs.append({
                "category": r.get("pillar", "General"),
                "title": r.get("item", "Issue"),
                "description": r.get("recommendation", ""),
                "priority": "High" if report.get("overall_score", 100) < 50 else "Medium",
                "status": "Open"
            })
            
        audit_report_dict = {
            "website_url": report["url"],
            "user_id": str(current_user["_id"]),
            "user_name": current_user["full_name"],
            "scan_type": "Full Audit",
            "audit_score": report["overall_score"],
            "category_scores": report["pillar_scores"],
            "recommendations": mapped_recs,
            "issues_found": len(mapped_recs),
            "scan_status": "Completed"
        }
        
        await process_audit_workflow(audit_report_dict, db)
        
        print("Returning response")
        logger.info(f"Successfully processed workflow for {url}")
        return report
    except Exception as e:
        print("EXCEPTION ENCOUNTERED:")
        print(traceback.format_exc())
        logger.error(f"Error scanning website {url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scan/{scan_id}", response_model=AuditReportResponse)
async def get_scan_report(scan_id: str, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(scan_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid scan ID format.")
    
    report = await db["scans"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Scan report not found.")
    
    return serialize_doc(report)

@router.post("/visitor")
async def log_visitor(payload: VisitorCreate, request: Request, db=Depends(get_database)):
    # Get client IP address
    ip_address = request.headers.get("x-forwarded-for")
    if ip_address:
        # If there are multiple IPs in proxy header, get the first one
        ip_address = ip_address.split(",")[0].strip()
    else:
        ip_address = request.client.host if request.client else "127.0.0.1"

    visitor_log = {
        "ip_address": ip_address,
        "browser": payload.browser,
        "device": payload.device,
        "referrer": payload.referrer,
        "page_visited": payload.page_visited,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    result = await db["visitor_logs"].insert_one(visitor_log)
    visitor_log["_id"] = str(result.inserted_id)
    return serialize_doc(visitor_log)

@router.post("/lead")
async def capture_lead(payload: LeadCreate, db=Depends(get_database)):
    lead = {
        "name": payload.name.strip(),
        "email": payload.email.strip().lower(),
        "website_url": payload.website_url.strip(),
        "audit_score": payload.audit_score,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    
    # Check if lead for this email and url already exists
    existing = await db["leads"].find_one({"email": lead["email"], "website_url": lead["website_url"]})
    if existing:
        return serialize_doc(existing)

    result = await db["leads"].insert_one(lead)
    lead["_id"] = str(result.inserted_id)
    return serialize_doc(lead)

@router.delete("/lead/{lead_id}")
async def delete_lead(lead_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(lead_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid lead ID format.")
    
    result = await db["leads"].delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found.")
    
    return {"success": True, "message": "Lead deleted successfully."}

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    # Get total counts
    total_visitors = await db["visitor_logs"].count_documents({})
    total_scans = await db["scans"].count_documents({})
    total_leads = await db["leads"].count_documents({})

    # Get recent lists
    recent_leads_cursor = db["leads"].find().sort("created_at", -1).limit(5)
    recent_leads = await recent_leads_cursor.to_list(length=5)

    recent_visitors_cursor = db["visitor_logs"].find().sort("created_at", -1).limit(5)
    recent_visitors = await recent_visitors_cursor.to_list(length=5)

    # Aggregations for Scans by Day (last 7 days)
    # Filter for scans in last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    scans_pipeline = [
        {"$match": {"created_at": {"$gte": seven_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    scans_by_day_data = await db["scans"].aggregate(scans_pipeline).to_list(length=7)
    scans_by_day = [DailyCount(date=item["_id"], count=item["count"]) for item in scans_by_day_data]

    # Aggregations for Leads by Day
    leads_pipeline = [
        {"$match": {"created_at": {"$gte": seven_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    leads_by_day_data = await db["leads"].aggregate(leads_pipeline).to_list(length=7)
    leads_by_day = [DailyCount(date=item["_id"], count=item["count"]) for item in leads_by_day_data]

    # Fallback to empty list or fill dates if necessary
    # If no data exists, we can provide a default sorted structure
    if not scans_by_day:
        scans_by_day = []
    if not leads_by_day:
        leads_by_day = []

    return DashboardStats(
        total_visitors=total_visitors,
        total_scans=total_scans,
        total_leads=total_leads,
        recent_leads=serialize_list(recent_leads),
        recent_visitors=serialize_list(recent_visitors),
        scans_by_day=scans_by_day,
        leads_by_day=leads_by_day
    )

@router.get("/dashboard/leads", response_model=List[Lead])
async def get_all_leads(db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    leads_cursor = db["leads"].find().sort("created_at", -1)
    leads = await leads_cursor.to_list(length=500)
    return serialize_list(leads)

@router.get("/dashboard/visitors", response_model=List[VisitorLog])
async def get_recent_visitors(db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    visitors_cursor = db["visitor_logs"].find().sort("created_at", -1).limit(100)
    visitors = await visitors_cursor.to_list(length=100)
    return serialize_list(visitors)
