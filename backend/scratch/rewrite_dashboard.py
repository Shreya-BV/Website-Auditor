import os

file_path = "app/routes/api.py"

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if line.startswith("@router.get(\"/dashboard/stats\""):
        start_idx = i
    if start_idx != -1 and line.startswith("@router.get(\"/dashboard/leads\""):
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_func = """@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Base counts
    total_visitors = await db["visitor_logs"].count_documents({})
    total_scans = await db["scans"].count_documents({})
    total_audits = await db["audit_reports"].count_documents({})
    total_leads = await db["leads"].count_documents({})

    visitors_today = await db["visitor_logs"].count_documents({"created_at": {"$gte": today_start}})
    leads_today = await db["leads"].count_documents({"created_at": {"$gte": today_start}})
    
    conversion_rate = 0.0
    if total_visitors > 0:
        conversion_rate = round((total_leads / total_visitors) * 100, 2)

    # Aggregations for Average Score & Average Scan Time
    avg_pipeline = [
        {"$group": {
            "_id": None, 
            "avg_score": {"$avg": "$audit_score"},
            "avg_time": {"$avg": "$performance_metrics.total_time_ms"}
        }}
    ]
    avg_data = await db["audit_reports"].aggregate(avg_pipeline).to_list(length=1)
    average_score = round(avg_data[0]["avg_score"], 1) if avg_data and avg_data[0].get("avg_score") else 0.0
    average_scan_time_ms = round(avg_data[0]["avg_time"], 1) if avg_data and avg_data[0].get("avg_time") else 0.0

    # Top Performing Website
    top_site_data = await db["audit_reports"].find().sort("audit_score", -1).limit(1).to_list(length=1)
    top_performing_website = top_site_data[0]["website_url"] if top_site_data else "N/A"

    # Most Common Issue (simplified counting from recommendations)
    # We unwind recommendations and group by title
    issue_pipeline = [
        {"$unwind": "$recommendations"},
        {"$group": {"_id": "$recommendations.title", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    issue_data = await db["audit_reports"].aggregate(issue_pipeline).to_list(length=1)
    most_common_issue = issue_data[0]["_id"] if issue_data else "N/A"

    # Most Missing Feature (from technology_detections where found=False)
    tech_pipeline = [
        {"$unwind": "$technology_detections"},
        {"$match": {"technology_detections.found": False}},
        {"$group": {"_id": "$technology_detections.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ]
    tech_data = await db["audit_reports"].aggregate(tech_pipeline).to_list(length=1)
    most_missing_feature = tech_data[0]["_id"] if tech_data else "N/A"

    # Recent Data
    recent_leads = await db["leads"].find().sort("created_at", -1).limit(5).to_list(length=5)
    recent_visitors = await db["visitor_logs"].find().sort("created_at", -1).limit(5).to_list(length=5)

    # By Day Data
    seven_days_ago = now - timedelta(days=7)
    
    def get_day_pipeline():
        return [
            {"$match": {"created_at": {"$gte": seven_days_ago}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        
    scans_by_day_data = await db["audit_reports"].aggregate(get_day_pipeline()).to_list(length=7)
    scans_by_day = [DailyCount(date=item["_id"], count=item["count"]) for item in scans_by_day_data]

    leads_by_day_data = await db["leads"].aggregate(get_day_pipeline()).to_list(length=7)
    leads_by_day = [DailyCount(date=item["_id"], count=item["count"]) for item in leads_by_day_data]

    return DashboardStats(
        total_visitors=total_visitors,
        total_scans=total_scans,
        total_leads=total_leads,
        average_score=average_score,
        total_audits=total_audits,
        visitors_today=visitors_today,
        leads_today=leads_today,
        conversion_rate=conversion_rate,
        average_scan_time_ms=average_scan_time_ms,
        most_common_issue=most_common_issue,
        most_missing_feature=most_missing_feature,
        top_performing_website=top_performing_website,
        recent_leads=serialize_list(recent_leads),
        recent_visitors=serialize_list(recent_visitors),
        scans_by_day=scans_by_day,
        leads_by_day=leads_by_day
    )

"""
    lines[start_idx:end_idx] = [new_func]
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Dashboard endpoint rewritten successfully.")
else:
    print("Could not find the function boundaries!")
