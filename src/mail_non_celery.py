import httpx
from src.config import Config

async def send_email_via_api(recipients:list[str], subject:str, body:str):
    # Example using Resend's API
    # headers = {
    #     "Authorization": f"Bearer {Config.MAIL_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    # data = {
    #     "from": f"{Config.MAIL_FROM_NAME} <{Config.MAIL_FROM}>",
    #     "to": recipients,
    #     "subject": subject,
    #     "html": body
    # }
    
    # # Port 443 is used here, so Render will allow it
    # with httpx.Client() as client:
    #     client.post("https://api.resend.com/emails", headers=headers, json=data)
    
    url = "https://api.brevo.com/v3/smtp/email"
    
    headers = {
        "accept": "application/json",
        "api-key": Config.MAIL_API_KEY,
        "content-type": "application/json"
    }
    
    payload = {
        "sender": {"name": Config.MAIL_FROM_NAME, "email": Config.MAIL_FROM},
        "to": [{"email": recipient} for recipient in recipients],
        "subject": subject,
        "htmlContent": body
    }
    
    # Send the request asynchronously
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()  # This will log an error if the API rejects the email