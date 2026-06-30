import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.email_service import send_audit_email

async def test():
    # Setup dummy pdf
    pdf_path = "test_dummy.pdf"
    with open(pdf_path, "w") as f:
        f.write("dummy pdf content")
        
    print("Testing email delivery...")
    success, msg = await send_audit_email(
        to_email="test@example.com",
        user_name="Test User",
        website_url="https://example.com",
        audit_score=95,
        pdf_path=pdf_path
    )
    
    print(f"Result - Success: {success}, Message: {msg}")
    
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

if __name__ == "__main__":
    asyncio.run(test())
