import os
import sys
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from app.services.email_sender import get_graph_token
from app.core.config import settings
import httpx

async def check_subscriptions():
    token = await get_graph_token()
    if not token:
        print("Failed to get token!")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("Checking active Microsoft Graph Subscriptions...")
    async with httpx.AsyncClient() as client:
        response = await client.get("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)
        if response.status_code == 200:
            data = response.json()
            subs = data.get("value", [])
            if not subs:
                print("NO ACTIVE SUBSCRIPTIONS FOUND. The webhook did not register successfully.")
            else:
                for sub in subs:
                    print(f"Subscription ID: {sub.get('id')}")
                    print(f"  Resource: {sub.get('resource')}")
                    print(f"  Notification URL: {sub.get('notificationUrl')}")
                    print(f"  Expiration: {sub.get('expirationDateTime')}")
                    print("-" * 40)
        else:
            print(f"Failed to fetch subscriptions: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(check_subscriptions())
