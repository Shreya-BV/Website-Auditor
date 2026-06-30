import os
import smtplib
import logging
from email.message import EmailMessage
import mimetypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_audit_email(to_email: str, user_name: str, website_url: str, audit_score: int, pdf_path: str, max_retries: int = 3):
    """
    Send the audit report PDF to the user's email using SMTP.
    Handles failures gracefully and retries if necessary.
    """
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_pass = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_pass:
        logger.warning("SMTP credentials not found in environment variables. Falling back to mock email.")
        logger.info(f"MOCK EMAIL: Would send {pdf_path} to {to_email} for {website_url} with score {audit_score}")
        return False

    from_email = os.environ.get("FROM_EMAIL", smtp_user)

    msg = EmailMessage()
    msg['Subject'] = f'Website Audit Report – {website_url}'
    msg['From'] = from_email
    msg['To'] = to_email

    body = f"""Hello {user_name},

Thank you for using Website Auditor.

Your website audit has been completed successfully.

The professional audit report is attached.

The report includes:
Overall Website Score
Five Pillars
Business Impact
Recommendations
Priority Issues
Technology Detection
Improvement Roadmap

If you need assistance implementing the recommendations, please contact us.

Regards,

Website Auditor Team"""
    msg.set_content(body)

    # Attach the PDF
    if os.path.exists(pdf_path):
        ctype, encoding = mimetypes.guess_type(pdf_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        with open(pdf_path, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(pdf_path))
    else:
        logger.error(f"Failed to attach PDF: File not found at {pdf_path}")
        return False

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[EMAIL SERVICE] Attempting to send email to {to_email} (Attempt {attempt}/{max_retries})")
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()
            logger.info(f"[EMAIL SERVICE] SMTP Connected to {smtp_host}:{smtp_port}")
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            logger.info(f"[EMAIL SERVICE] Email successfully sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Email delivery failed on attempt {attempt}: {e}")
            if attempt == max_retries:
                logger.error(f"Max retries reached. Failed to send email to {to_email}.")
                return False
    return False
