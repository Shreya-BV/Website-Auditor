import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_audit_email(to_email: str, user_name: str, website_url: str, audit_score: int, pdf_path: str):
    """
    Mock email service to send the audit report.
    Logs the email details to the console instead of actually sending it.
    """
    logger.info("="*50)
    logger.info("MOCK EMAIL SENDER ACTIVATED")
    logger.info("="*50)
    logger.info(f"To: {to_email}")
    logger.info(f"Subject: Your Website Audit Report is Ready")
    logger.info("Body:")
    logger.info(f"  Hello {user_name},")
    logger.info(f"  Your website audit has been completed successfully.")
    logger.info(f"  Website: {website_url}")
    logger.info(f"  Audit Score: {audit_score}")
    logger.info(f"  Please find your detailed audit report attached.")
    logger.info("  Regards,")
    logger.info("  Website Auditor Team")
    logger.info(f"Attachment Included: {pdf_path}")
    logger.info("="*50)
    
    # In a real scenario, use aiosmtplib and email.message here
    return True
