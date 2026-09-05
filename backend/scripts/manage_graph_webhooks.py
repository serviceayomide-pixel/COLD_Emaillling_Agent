import asyncio
import httpx
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the parent directory to sys.path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.imap_reader import get_graph_token

async def manage_webhooks():
    """Checks for existing MS Graph Webhooks and renews or creates them.
    
    Strategy:
    - Try to renew existing subscriptions first.
    - If renewal fails (expired/corrupted), delete the old one and create fresh.
    - This ensures webhooks NEVER stay dead, even after a long outage.
    """
    print("Managing MS Graph Webhooks...")
    token = await get_graph_token()
    if not token:
        print("Failed to authenticate with Microsoft Graph.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Tracking base URL is required
    base_url = settings.TRACKING_BASE_URL
    if not base_url or "localhost" in base_url or "127.0.0.1" in base_url:
        print("WARNING: TRACKING_BASE_URL is missing or is localhost. Microsoft Graph requires a public HTTPS URL.")
        print("If you are running locally, use ngrok or similar and update TRACKING_BASE_URL.")
        return

    if not base_url.startswith("http://") and not base_url.startswith("https://"):
        base_url = f"https://{base_url}"

    notification_url = f"{base_url.rstrip('/')}/api/webhooks/graph"
    email_address = settings.MICROSOFT_EMAIL

    if not email_address:
        print("MICROSOFT_EMAIL is not set in environment.")
        return

    # Webhooks expire after 4230 minutes max (~2.9 days). Set expiration to 2.5 days.
    expiration = (datetime.now(timezone.utc) + timedelta(days=2, hours=12)).isoformat()

    resources_to_subscribe = {
        "inbox": f"users/{email_address}/mailFolders('inbox')/messages",
        "sentitems": f"users/{email_address}/mailFolders('sentitems')/messages"
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        # 1. Get existing subscriptions
        resp = await client.get("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)
        existing_subscriptions = []
        if resp.status_code == 200:
            existing_subscriptions = resp.json().get("value", [])
        else:
            print(f"Error fetching existing subscriptions: {resp.text}")

        # 2. Renew or Create for each folder
        for folder, resource in resources_to_subscribe.items():
            # Find if we already have a subscription for this resource
            sub = next((s for s in existing_subscriptions if s.get("resource") == resource), None)
            
            if sub:
                sub_id = sub["id"]
                print(f"Found existing subscription for {folder} (ID: {sub_id}). Renewing...")
                
                payload = {
                    "expirationDateTime": expiration
                }
                patch_resp = await client.patch(
                    f"https://graph.microsoft.com/v1.0/subscriptions/{sub_id}",
                    headers=headers,
                    json=payload
                )
                if patch_resp.status_code == 200:
                    print(f"Successfully renewed webhook for {folder}.")
                else:
                    print(f"Failed to renew webhook for {folder}: {patch_resp.status_code} - {patch_resp.text}")
                    print(f"Deleting expired subscription and recreating...")
                    
                    # Delete the broken/expired subscription
                    del_resp = await client.delete(
                        f"https://graph.microsoft.com/v1.0/subscriptions/{sub_id}",
                        headers=headers
                    )
                    if del_resp.status_code in [200, 204]:
                        print(f"Deleted old subscription for {folder}.")
                    else:
                        print(f"Warning: Could not delete old subscription: {del_resp.text}")
                    
                    # Create a fresh one
                    await _create_subscription(client, headers, folder, resource, notification_url, expiration)
            else:
                print(f"No existing subscription for {folder}. Creating new one...")
                await _create_subscription(client, headers, folder, resource, notification_url, expiration)


async def _create_subscription(client, headers, folder, resource, notification_url, expiration):
    """Helper to create a new MS Graph webhook subscription."""
    payload = {
        "changeType": "created",
        "notificationUrl": notification_url,
        "resource": resource,
        "expirationDateTime": expiration,
        "clientState": settings.WEBHOOK_SECRET,
        "latestSupportedTlsVersion": "v1_2"
    }
    
    post_resp = await client.post(
        "https://graph.microsoft.com/v1.0/subscriptions",
        headers=headers,
        json=payload
    )
    if post_resp.status_code in [200, 201]:
        print(f"Successfully created webhook for {folder}.")
    else:
        print(f"Failed to create webhook for {folder}: {post_resp.status_code} - {post_resp.text}")


if __name__ == "__main__":
    asyncio.run(manage_webhooks())
