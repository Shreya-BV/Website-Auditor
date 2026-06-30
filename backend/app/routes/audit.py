import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from app.database.mongodb import get_database
from app.schemas.audit_report import AuditReport
from app.services.pdf_generator import generate_audit_pdf
from app.services.email_service import send_audit_email
from app.routes.auth import get_current_user

router = APIRouter()

def serialize_doc(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

DEBUG_REPORT_FLOW = os.environ.get("DEBUG_REPORT_FLOW", "False").lower() == "true"

async def process_audit_workflow(report_dict: dict, db) -> dict:
    if DEBUG_REPORT_FLOW:
        print(f"[DEBUG_REPORT_FLOW] Starting workflow for URL: {report_dict.get('website_url')}")
    report_dict["created_at"] = datetime.now(timezone.utc)
    report_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Store in database
    result = await db["audit_reports"].insert_one(report_dict)
    inserted_id = str(result.inserted_id)
    report_dict["_id"] = inserted_id
    

    if DEBUG_REPORT_FLOW:
        print(f"[DEBUG_REPORT_FLOW] PDF Generation Started for Report ID: {inserted_id}")
    
    # Generate PDF locally first
    pdf_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"audit_{inserted_id}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    generate_audit_pdf(report_dict, pdf_path)
    
    if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
        if DEBUG_REPORT_FLOW:
            print("[DEBUG_REPORT_FLOW] PDF missing or empty. Regenerating automatically...")
        generate_audit_pdf(report_dict, pdf_path)
        
    # Read PDF and save to GridFS
    fs = AsyncIOMotorGridFSBucket(db)
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
        
    grid_in = fs.open_upload_stream(pdf_filename, metadata={"audit_id": inserted_id})
    await grid_in.write(pdf_bytes)
    await grid_in.close()
    pdf_gridfs_id = str(grid_in._id)
    
    # Clean up ephemeral local file
    try:
        os.remove(pdf_path)
    except Exception:
        pass
    
    # Update PDF metadata in DB
    report_dict["pdf_gridfs_id"] = pdf_gridfs_id
    report_dict["pdf_filename"] = pdf_filename
    report_dict["pdf_generated"] = True
    report_dict["download_count"] = 0
    report_dict["pdf_url"] = f"/api/audit/download/{inserted_id}"
    await db["audit_reports"].update_one(
        {"_id": ObjectId(inserted_id)}, 
        {"$set": {
            "pdf_gridfs_id": pdf_gridfs_id,
            "pdf_filename": pdf_filename,
            "pdf_generated": True,
            "download_count": 0,
            "pdf_url": report_dict["pdf_url"]
        }}
    )
    
    # Send email
    user_email = report_dict.get("email")
    if user_email:
        if DEBUG_REPORT_FLOW:
            print(f"[DEBUG_REPORT_FLOW] Queuing Email for {user_email}")
            
        email_success, email_msg = await send_audit_email(
            to_email=user_email,
            user_name=report_dict.get("user_name", "User"),
            website_url=report_dict.get("website_url"),
            audit_score=report_dict.get("audit_score"),
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename
        )
        
        delivery_status = "sent" if email_success else "failed"
        sent_at = datetime.now(timezone.utc) if email_success else None
        
        if DEBUG_REPORT_FLOW:
            print(f"[DEBUG_REPORT_FLOW] Email Delivery Status to {user_email}: {delivery_status}, Message: {email_msg}")
            
        email_delivery_record = {
            "audit_id": inserted_id,
            "user_id": report_dict.get("user_id"),
            "user_email": user_email,
            "website_url": report_dict.get("website_url"),
            "subject": f"Website Audit Report – {report_dict.get('website_url')}",
            "pdf_filename": pdf_filename,
            "email_provider": "SMTP_GMAIL",
            "delivery_status": delivery_status,
            "retry_count": 0,
            "sent_at": sent_at,
            "failure_reason": None if email_success else email_msg,
            "created_at": datetime.now(timezone.utc)
        }
        
        await db["email_delivery"].insert_one(email_delivery_record)
        
        report_dict["email_sent"] = email_success
        report_dict["email_sent_at"] = sent_at
        report_dict["delivery_status"] = delivery_status
        report_dict["error_message"] = None if email_success else email_msg
        
        import uuid
        message_id = str(uuid.uuid4()) if email_success else None
        
        await db["audit_reports"].update_one(
            {"_id": ObjectId(inserted_id)},
            {"$set": {
                "email_sent": email_success,
                "email_sent_at": sent_at,
                "delivery_status": delivery_status,
                "error_message": None if email_success else email_msg,
                "message_id": message_id
            }}
        )
        
    return report_dict

@router.post("/create", response_model=AuditReport)
async def create_audit_report(payload: AuditReport, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    report_dict = payload.dict(by_alias=True, exclude_none=True)
    report_dict["user_id"] = str(current_user["_id"])
    report_dict["user_name"] = current_user.get("full_name", "")
    report_dict = await process_audit_workflow(report_dict, db)
    return serialize_doc(report_dict)


@router.get("/history", response_model=List[AuditReport])
async def get_audit_history(db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    # Filter by user_id
    cursor = db["audit_reports"].find({"user_id": str(current_user["_id"])}).sort("created_at", -1)
    reports = await cursor.to_list(length=100)
    return [serialize_doc(r) for r in reports]

@router.get("/{audit_id}", response_model=AuditReport)
async def get_audit_report(audit_id: str, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    return serialize_doc(report)

@router.get("/download/{audit_id}")
async def download_audit_pdf(audit_id: str, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report or not report.get("pdf_gridfs_id"):
        raise HTTPException(status_code=404, detail="PDF not found.")
        
    gridfs_id = ObjectId(report["pdf_gridfs_id"])
    fs = AsyncIOMotorGridFSBucket(db)
    
    try:
        grid_out = await fs.open_download_stream(gridfs_id)
    except Exception:
        raise HTTPException(status_code=404, detail="PDF file missing from database.")
        
    # Increment download count
    await db["audit_reports"].update_one({"_id": oid}, {"$inc": {"download_count": 1}})
        
    website_url = report.get("website_url", "unknown")
    clean_url = website_url.replace("https://", "").replace("http://", "").replace("www.", "").replace(".", "-").replace("/", "").strip("-")
    date_str = report.get("created_at", datetime.now(timezone.utc)).strftime("%Y-%m-%d") if isinstance(report.get("created_at"), datetime) else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    download_filename = f"website-audit-{clean_url}-{date_str}.pdf"
        
    async def pdf_generator():
        while True:
            chunk = await grid_out.read(1024 * 1024)
            if not chunk:
                break
            yield chunk
            
    return StreamingResponse(
        pdf_generator(), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )

@router.post("/retry-email/{audit_id}")
async def retry_audit_email(audit_id: str, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    if report.get("user_id") != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to retry this email.")
        
    user_email = report.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="No email address associated with this report.")
        
    fs = AsyncIOMotorGridFSBucket(db)
    pdf_gridfs_id = report.get("pdf_gridfs_id")
    pdf_filename = report.get("pdf_filename", f"audit_{oid}.pdf")
    
    pdf_bytes = None
    if pdf_gridfs_id:
        try:
            grid_out = await fs.open_download_stream(ObjectId(pdf_gridfs_id))
            pdf_bytes = await grid_out.read()
        except Exception:
            pass
            
    if not pdf_bytes:
        print("[DEBUG_REPORT_FLOW] PDF missing in DB on retry, generating automatically...")
        pdf_dir = os.path.join(os.getcwd(), "reports")
        os.makedirs(pdf_dir, exist_ok=True)
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        generate_audit_pdf(report, pdf_path)
        
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
            
        grid_in = fs.open_upload_stream(pdf_filename, metadata={"audit_id": str(oid)})
        await grid_in.write(pdf_bytes)
        await grid_in.close()
        pdf_gridfs_id = str(grid_in._id)
        
        try:
            os.remove(pdf_path)
        except:
            pass
        
        # Ensure the new path is updated in DB just in case
        await db["audit_reports"].update_one(
            {"_id": oid},
            {"$set": {"pdf_gridfs_id": pdf_gridfs_id, "pdf_filename": pdf_filename, "pdf_generated": True}}
        )
        
    email_success, email_msg = await send_audit_email(
        to_email=user_email,
        user_name=report.get("user_name", "User"),
        website_url=report.get("website_url"),
        audit_score=report.get("audit_score"),
        pdf_bytes=pdf_bytes,
        pdf_filename=pdf_filename
    )
    
    delivery_status = "sent" if email_success else "failed"
    sent_at = datetime.now(timezone.utc) if email_success else None
    
    await db["email_delivery"].update_one(
        {"audit_id": audit_id},
        {
            "$inc": {"retry_count": 1},
            "$set": {
                "delivery_status": delivery_status,
                "sent_at": sent_at,
                "failure_reason": None if email_success else email_msg
            }
        }
    )
    
    import uuid
    message_id = str(uuid.uuid4()) if email_success else None
    
    await db["audit_reports"].update_one(
        {"_id": oid},
        {"$set": {
            "email_sent": email_success,
            "email_sent_at": sent_at,
            "delivery_status": delivery_status,
            "error_message": None if email_success else email_msg,
            "message_id": message_id
        }}
    )
    
    if not email_success:
        return {"success": False, "message": email_msg}
    
    return {"success": True, "message": "Email sent successfully on retry."}

@router.get("/email-status/{audit_id}")
async def get_email_status(audit_id: str, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    if report.get("user_id") != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized to view this email status.")
        
    delivery_record = await db["email_delivery"].find_one({"audit_id": audit_id})
    if not delivery_record:
        return {"delivery_status": report.get("delivery_status", "unknown")}
        
    return serialize_doc(delivery_record)

@router.delete("/{audit_id}")
async def delete_audit_report(audit_id: str, db=Depends(get_database), current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    pdf_gridfs_id = report.get("pdf_gridfs_id")
    if pdf_gridfs_id:
        try:
            fs = AsyncIOMotorGridFSBucket(db)
            await fs.delete(ObjectId(pdf_gridfs_id))
        except Exception as e:
            print(f"Error removing PDF from GridFS: {e}")
            
    await db["audit_reports"].delete_one({"_id": oid})
    
    return {"success": True, "message": "Audit report deleted successfully."}
