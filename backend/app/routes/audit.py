import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

from app.database.mongodb import get_database
from app.schemas.audit_report import AuditReport
from app.services.pdf_generator import generate_audit_pdf
from app.services.email_service import send_audit_email

router = APIRouter()

def serialize_doc(doc):
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def process_audit_workflow(report_dict: dict, db) -> dict:
    report_dict["created_at"] = datetime.now(timezone.utc)
    report_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Store in database
    result = await db["audit_reports"].insert_one(report_dict)
    inserted_id = str(result.inserted_id)
    report_dict["_id"] = inserted_id
    
    # Generate PDF
    pdf_dir = os.path.join(os.getcwd(), "reports")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_filename = f"audit_{inserted_id}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_filename)
    
    generate_audit_pdf(report_dict, pdf_path)
    
    # Update PDF path in DB
    report_dict["pdf_path"] = pdf_path
    report_dict["pdf_url"] = f"/api/audit/download/{inserted_id}"
    await db["audit_reports"].update_one(
        {"_id": ObjectId(inserted_id)}, 
        {"$set": {"pdf_path": pdf_path, "pdf_url": report_dict["pdf_url"]}}
    )
    
    # Send email
    user_email = report_dict.get("email")
    if user_email:
        await send_audit_email(
            to_email=user_email,
            user_name=report_dict.get("user_name", "User"),
            website_url=report_dict.get("website_url"),
            audit_score=report_dict.get("audit_score"),
            pdf_path=pdf_path
        )
        report_dict["email_sent"] = True
        await db["audit_reports"].update_one(
            {"_id": ObjectId(inserted_id)},
            {"$set": {"email_sent": True}}
        )
        
    return report_dict

@router.post("/create", response_model=AuditReport)
async def create_audit_report(payload: AuditReport, db=Depends(get_database)):
    report_dict = payload.dict(by_alias=True, exclude_none=True)
    report_dict = await process_audit_workflow(report_dict, db)
    return serialize_doc(report_dict)


@router.get("/history", response_model=List[AuditReport])
async def get_audit_history(db=Depends(get_database)):
    cursor = db["audit_reports"].find().sort("created_at", -1)
    reports = await cursor.to_list(length=100)
    return [serialize_doc(r) for r in reports]

@router.get("/{audit_id}", response_model=AuditReport)
async def get_audit_report(audit_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    return serialize_doc(report)

@router.get("/download/{audit_id}")
async def download_audit_pdf(audit_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report or not report.get("pdf_path"):
        raise HTTPException(status_code=404, detail="PDF not found.")
        
    pdf_path = report["pdf_path"]
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file missing from server.")
        
    return FileResponse(pdf_path, media_type="application/pdf", filename=os.path.basename(pdf_path))

@router.post("/send-email/{audit_id}")
async def resend_audit_email(audit_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    user_email = report.get("email")
    if not user_email:
        raise HTTPException(status_code=400, detail="No email address associated with this report.")
        
    pdf_path = report.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file missing.")
        
    await send_audit_email(
        to_email=user_email,
        user_name=report.get("user_name", "User"),
        website_url=report.get("website_url"),
        audit_score=report.get("audit_score"),
        pdf_path=pdf_path
    )
    
    await db["audit_reports"].update_one(
        {"_id": oid},
        {"$set": {"email_sent": True}}
    )
    
    return {"success": True, "message": "Email sent successfully."}

@router.delete("/{audit_id}")
async def delete_audit_report(audit_id: str, db=Depends(get_database)):
    try:
        oid = ObjectId(audit_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid audit ID format.")
        
    report = await db["audit_reports"].find_one({"_id": oid})
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found.")
        
    pdf_path = report.get("pdf_path")
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception as e:
            print(f"Error removing PDF: {e}")
            
    await db["audit_reports"].delete_one({"_id": oid})
    
    return {"success": True, "message": "Audit report deleted successfully."}
