import asyncio
import httpx
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.imap_reader import get_graph_token

async def delete_webhooks():
    print("Fetching existing MS Graph Webhooks...")
    token = await get_graph_token()
    if not token:
        print("Failed to authenticate.")
        return

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get("https://graph.microsoft.com/v1.0/subscriptions", headers=headers)
        if resp.status_code == 200:
            subs = resp.json().get("value", [])
            if not subs:
                print("No subscriptions found to delete.")
                return
            for sub in subs:
                sub_id = sub["id"]
                print(f"Deleting subscription {sub_id}...")
                del_resp = await client.delete(f"https://graph.microsoft.com/v1.0/subscriptions/{sub_id}", headers=headers)
                if del_resp.status_code == 204:
                    print(f"Successfully deleted {sub_id}")
                else:
                    print(f"Failed to delete {sub_id}: {del_resp.status_code} - {del_resp.text}")
        else:
            print(f"Failed to fetch: {resp.text}")

if __name__ == "__main__":
    asyncio.run(delete_webhooks())
