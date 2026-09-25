import asyncio
import httpx
import os
import sys

# Add backend to path so we can import config
sys.path.append(os.path.join(os.getcwd(), "backend"))
from dotenv import load_dotenv

load_dotenv(os.path.join("backend", ".env"))

TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
USER_EMAIL = os.getenv("MICROSOFT_EMAIL")

async def get_graph_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "client_id": CLIENT_ID,
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

async def check_api():
    print("--------------------------------------------------")
    print("Checking Microsoft Graph API Connection Status...")
    print("--------------------------------------------------")
    try:
        token = await get_graph_token()
        print("[SUCCESS] 1. Authentication successful! (App has permissions to talk to Microsoft)")
        
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient() as client:
            # Check user access (Sending capability)
            user_resp = await client.get(f"https://graph.microsoft.com/v1.0/users/{USER_EMAIL}", headers=headers)
            if user_resp.status_code == 200:
                print(f"[SUCCESS] 2. Sending Connection Active (Mailbox '{USER_EMAIL}' is accessible)")
            else:
                print(f"[ERROR] 2. Failed to access mailbox: {user_resp.text}")

            # Check Webhook Subscriptions (Receiving capability)
            sub_resp = await client.get("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)
            if sub_resp.status_code == 200:
                subs = sub_resp.json().get("value", [])
                if len(subs) > 0:
                    print(f"[SUCCESS] 3. Receiving Connection Active ({len(subs)} webhook subscriptions found)")
                    for s in subs:
                        print(f"    -> Listening to: {s.get('resource')} ")
                        print(f"    -> Forwarding to your Railway URL: {s.get('notificationUrl')}")
                        print(f"    -> Expiration: {s.get('expirationDateTime')}")
                else:
                    print("[WARNING] 3. No active webhooks found. (If you just restarted Railway, wait 60 seconds for the background task to register them).")
            else:
                print(f"[ERROR] 3. Failed to check webhooks: {sub_resp.text}")

    except Exception as e:
        print(f"[ERROR] Error during check: {e}")
    print("--------------------------------------------------")

if __name__ == "__main__":
    asyncio.run(check_api())
