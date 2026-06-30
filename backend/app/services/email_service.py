import os
import smtplib
import logging
from email.message import EmailMessage
import mimetypes
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_audit_email(to_email: str, user_name: str, website_url: str, audit_score: int, pdf_path: str, max_retries: int = 3):
    """
    Send the audit report PDF to the user's email using SMTP.
    Handles failures gracefully and retries if necessary.
    Returns: (bool, str) - (Success status, Error message or "Success")
    """
    logger.info(f"[EMAIL SERVICE] Preparing to send email to {to_email} for {website_url}")
    
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_pass = os.environ.get("SMTP_PASSWORD")

    if not smtp_user or not smtp_pass:
        logger.error("[EMAIL SERVICE] SMTP credentials not found in environment variables. Failing.")
        return False, "SMTP credentials not configured on the server."

    from_email = os.environ.get("FROM_EMAIL", smtp_user)

    logger.info(f"[EMAIL SERVICE] Configuration - Host: {smtp_host}:{smtp_port}, From: {from_email}, To: {to_email}")

    msg = EmailMessage()
    msg['Subject'] = f'Website Audit Report – {website_url}'
    msg['From'] = from_email
    msg['To'] = to_email

    logger.info(f"[EMAIL SERVICE] Constructed MIME message headers: Subject={msg['Subject']}, From={msg['From']}, To={msg['To']}")

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
    logger.info(f"[EMAIL SERVICE] Checking for PDF attachment at {pdf_path}")
    if os.path.exists(pdf_path):
        if os.path.getsize(pdf_path) == 0:
            error_msg = f"Failed to attach PDF: File at {pdf_path} is empty."
            logger.error(f"[EMAIL SERVICE] {error_msg}")
            return False, error_msg

        logger.info(f"[EMAIL SERVICE] PDF found. Attaching to email...")
        ctype, encoding = mimetypes.guess_type(pdf_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        try:
            with open(pdf_path, 'rb') as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=os.path.basename(pdf_path))
            logger.info(f"[EMAIL SERVICE] Attachment added successfully.")
        except Exception as e:
            error_msg = f"Error reading PDF file: {e}"
            logger.error(f"[EMAIL SERVICE] {error_msg}")
            logger.error(f"[EMAIL SERVICE] Exception Traceback:\n{traceback.format_exc()}")
            return False, error_msg
    else:
        error_msg = f"Failed to attach PDF: File not found at {pdf_path}"
        logger.error(f"[EMAIL SERVICE] {error_msg}")
        return False, error_msg

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"[EMAIL SERVICE] SMTP configuration loaded. Attempting to connect to SMTP server {smtp_host}:{smtp_port} (Attempt {attempt}/{max_retries})")
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            
            logger.info(f"[EMAIL SERVICE] Sending EHLO/HELO...")
            server.ehlo()
            
            logger.info(f"[EMAIL SERVICE] Starting TLS...")
            server.starttls()
            server.ehlo()
            
            logger.info(f"[EMAIL SERVICE] SMTP connected. Authenticating as {smtp_user}...")
            server.login(smtp_user, smtp_pass)
            logger.info(f"[EMAIL SERVICE] SMTP authenticated successfully.")
            
            logger.info(f"[EMAIL SERVICE] Sending message to {to_email}...")
            server.send_message(msg)
            
            logger.info(f"[EMAIL SERVICE] Quitting SMTP connection...")
            server.quit()
            
            logger.info(f"[EMAIL SERVICE] Email sent successfully to {to_email}")
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"[EMAIL SERVICE] SMTP Authentication Failed: {e}")
            logger.error(f"[EMAIL SERVICE] Exception Traceback:\n{traceback.format_exc()}")
            return False, f"SMTP Authentication Error: Check your username and app password."
        except Exception as e:
            logger.error(f"[EMAIL SERVICE] Email delivery failed on attempt {attempt}: {e}")
            logger.error(f"[EMAIL SERVICE] Exception Traceback:\n{traceback.format_exc()}")
            if attempt == max_retries:
                logger.error(f"[EMAIL SERVICE] Max retries reached. Failed to send email to {to_email}.")
                return False, f"SMTP Delivery Failed: {str(e)}"
    return False, "Unknown error during email delivery."
