import httpx
from typing import Dict
from app.core.config import settings

async def push_campaign_to_smtp_ghost(contact_email: str, contact_name: str, emails: Dict) -> bool:
    """
    Pushes the generated email sequence to SMTP Ghost.
    Requires you to map this to the exact SMTP Ghost API for creating/adding to a campaign.
    """
    # SMTP Ghost allows you to push custom fields simply by adding them to the JSON payload.
    # We will pass the full AI-generated subjects and bodies as custom variables.
    url = f"https://smtpghost.com/api/v1/lists/{settings.SMTP_GHOST_CAMPAIGN_ID}/contacts"
    
    headers = {
        "X-API-KEY": settings.SMTP_GHOST_API_KEY,
        "Content-Type": "application/json"
    }

    # Helper function to convert AI plain-text newlines to HTML <br> tags
    # so SMTP Ghost renders the paragraph breaks perfectly.
    def format_html(body_text: str) -> str:
        return body_text.replace('\n', '<br>')

    payload = {
        "contacts": [
            {
                "email": contact_email,
                "first_name": contact_name,
                "custom_fields": {
                    "email_1_subject": emails.get("email_1", {}).get("subject", "Quick Question"),
                    "email_1_body": format_html(emails.get("email_1", {}).get("body", "Hi, are you interested in our services?")),
                    
                    "email_2_subject": emails.get("email_2", {}).get("subject", "Following up"),
                    "email_2_body": format_html(emails.get("email_2", {}).get("body", "Just floating this to the top of your inbox.")),
                    
                    "email_3_subject": emails.get("email_3", {}).get("subject", "Any thoughts?"),
                    "email_3_body": format_html(emails.get("email_3", {}).get("body", "Wanted to check if you had time to review my previous email.")),
                    
                    "email_4_subject": emails.get("email_4", {}).get("subject", "Final follow up"),
                    "email_4_body": format_html(emails.get("email_4", {}).get("body", "I'll stop bugging you now. Let me know if things change."))
                }
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            if response.status_code in [200, 201]:
                return True
            print(f"SMTP Ghost API Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error pushing to SMTP Ghost: {e}")
        return False
