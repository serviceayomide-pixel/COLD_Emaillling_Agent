import httpx
from app.core.config import settings

async def get_graph_token() -> str:
    """Authenticates with Microsoft Azure AD to get a Graph API access token."""
    if not settings.MICROSOFT_TENANT_ID or not settings.MICROSOFT_CLIENT_ID or not settings.MICROSOFT_CLIENT_SECRET:
        print("Missing Microsoft OAuth credentials in .env")
        return None
        
    url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
    payload = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload, timeout=10.0)
            if response.status_code == 200:
                return response.json().get("access_token")
            else:
                print(f"Failed to get Graph Token: {response.text}")
                return None
    except Exception as e:
        print(f"Error fetching Graph Token: {e}")
        return None


async def fetch_unread_emails() -> list:
    """Fetches all unread emails from the inbox via Microsoft Graph API."""
    token = await get_graph_token()
    if not token:
        return []
        
    email_address = settings.MICROSOFT_EMAIL
    # Fetch recent messages, whether read or unread, to ensure we don't miss any if the user opens them
    url = f"https://graph.microsoft.com/v1.0/users/{email_address}/mailFolders/inbox/messages?$top=20"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    emails_data = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=15.0)
            if response.status_code == 200:
                messages = response.json().get("value", [])
                
                for msg in messages:
                    msg_id = msg.get("id")
                    subject = msg.get("subject", "")
                    sender_email = msg.get("from", {}).get("emailAddress", {}).get("address", "")
                    body = msg.get("bodyPreview", "")  # We can use bodyPreview or full body.content
                    
                    # Optional: Get full plain text body if available
                    if msg.get("body", {}).get("contentType") == "text":
                        body = msg.get("body", {}).get("content", body)
                        
                    emails_data.append({
                        "id": msg_id,
                        "subject": subject,
                        "sender_email": sender_email.lower(),
                        "body": body.strip()
                    })
                    
                    # Immediately mark as read so we don't process it again next tick
                    await mark_email_as_read(msg_id, token, email_address)
                    
            else:
                print(f"Graph API Error fetching emails: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error connecting to Graph API: {e}")
        
    return emails_data


async def mark_email_as_read(message_id: str, token: str, email_address: str):
    """Marks an email as read via Graph API."""
    url = f"https://graph.microsoft.com/v1.0/users/{email_address}/messages/{message_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"isRead": True}
    
    try:
        async with httpx.AsyncClient() as client:
            await client.patch(url, headers=headers, json=payload, timeout=10.0)
    except Exception as e:
        print(f"Failed to mark email {message_id} as read: {e}")
