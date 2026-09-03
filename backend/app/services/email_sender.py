import httpx
from app.core.config import settings
from app.services.imap_reader import get_graph_token


def inject_tracking_pixel(html_body: str, lead_id: int) -> str:
    """
    Injects an invisible 1x1 tracking pixel at the bottom of the email HTML.
    When the recipient opens the email, their client loads this image,
    which hits our /api/tracking/open/{lead_id} endpoint.
    """
    base_url = settings.TRACKING_BASE_URL
    if not base_url:
        return html_body  # No tracking URL configured, skip pixel

    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = f"https://{base_url}"

    pixel_url = f"{base_url}/api/tracking/open/{lead_id}"
    pixel_tag = (
        f'<img src="{pixel_url}" width="1" height="1" '
        f'style="display:none;width:1px;height:1px;border:0;" alt="" />'
    )
    return html_body + pixel_tag


async def send_email(to_email: str, subject: str, body: str, lead_id: int = None) -> bool:
    """
    Sends an individual email using the Microsoft Graph API.
    Bypasses traditional SMTP entirely.
    """
    token = await get_graph_token()
    if not token:
        print("Failed to get Graph API token. Cannot send email.")
        return False
        
    email_address = settings.MICROSOFT_EMAIL
    if not email_address:
        print("Missing MICROSOFT_EMAIL in .env. Cannot send email.")
        return False

    # Format the body to use HTML breaks for proper rendering
    html_body = body.replace('\n', '<br>')

    # Inject the invisible tracking pixel if we have a lead_id
    if lead_id is not None:
        html_body = inject_tracking_pixel(html_body, lead_id)

    url = f"https://graph.microsoft.com/v1.0/users/{email_address}/sendMail"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": html_body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=15.0)
            if response.status_code == 202:
                print(f"Graph API successfully sent email to {to_email}")
                return True
            else:
                print(f"Graph API failed to send email: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"Exception sending email via Graph API to {to_email}: {str(e)}")
        return False
