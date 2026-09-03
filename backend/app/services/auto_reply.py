import httpx
from app.core.config import settings
from app.services.imap_reader import get_graph_token

async def send_cal_link(recipient_email: str, message_id: str = None):
    """Sends the Cal.com booking link to an interested prospect via Microsoft Graph API."""
    
    token = await get_graph_token()
    if not token:
        print("Failed to get Graph API token. Cannot send auto-reply.")
        return False
        
    email_address = settings.MICROSOFT_EMAIL
    if not email_address:
        print("Missing MICROSOFT_EMAIL in .env. Cannot send auto-reply.")
        return False

    body = f"""Hi there,

Thanks for getting back to me! I'd love to chat and see how we can help your agency generate more private care enquiries.

You can grab a time that works best for you on my calendar here:
{settings.CAL_BOOKING_URL}

Looking forward to speaking with you!

Best regards,
"""

    html_body = body.replace('\n', '<br>')

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # If message_id is provided, reply directly to the existing thread message
    if message_id:
        url = f"https://graph.microsoft.com/v1.0/users/{email_address}/messages/{message_id}/reply"
        payload = {
            "comment": html_body
        }
    else:
        url = f"https://graph.microsoft.com/v1.0/users/{email_address}/sendMail"
        payload = {
            "message": {
                "subject": "Re: Let's schedule a call",
                "body": {
                    "contentType": "HTML",
                    "content": html_body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": recipient_email
                        }
                    }
                ]
            },
            "saveToSentItems": "true"
        }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            
            if response.status_code in [200, 201, 202]:
                print(f"Graph API successfully sent Cal.com link to {recipient_email} (Reply: {bool(message_id)})")
                return True
            else:
                # If reply failed and message_id was set, fall back to fresh email sending
                if message_id:
                    print(f"Graph API reply failed: {response.status_code} - {response.text}. Retrying with fresh email...")
                    return await send_cal_link(recipient_email, message_id=None)
                print(f"Graph API failed to send auto-reply: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Error sending auto-reply to {recipient_email} via Graph API: {e}")
        if message_id:
            print("Retrying with fresh email...")
            return await send_cal_link(recipient_email, message_id=None)
        return False
