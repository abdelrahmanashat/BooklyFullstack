import httpx
from src.config import Config

def send_email_via_api(recipients:list[str], subject:str, body:str):
    # Example using Resend's API
    headers = {
        "Authorization": f"Bearer {Config.MAIL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "from": f"{Config.MAIL_FROM_NAME} <{Config.MAIL_FROM}>",
        "to": recipients,
        "subject": subject,
        "html": body
    }
    
    # Port 443 is used here, so Render will allow it
    with httpx.Client() as client:
        client.post("https://api.resend.com/emails", headers=headers, json=data)