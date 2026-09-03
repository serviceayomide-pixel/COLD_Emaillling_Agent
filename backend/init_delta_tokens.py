import os
import httpx
import asyncio
from dotenv import load_dotenv
from app.core.config import settings
from app.services.imap_reader import get_graph_token
from app.core.database import SessionLocal
from app.models.models import SyncToken

load_dotenv()

async def initialize_delta_token(folder: str):
    token = await get_graph_token()
    if not token:
        print("Failed to get Graph token.")
        return
        
    email_address = settings.MICROSOFT_EMAIL
    
    # We only select minimal fields to make the initial history sync as fast as possible
    url = f"https://graph.microsoft.com/v1.0/users/{email_address}/mailFolders/{folder}/messages/delta?$select=id"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Initializing Delta Sync for {folder}...")
    
    db = SessionLocal()
    try:
        async with httpx.AsyncClient() as client:
            pages = 0
            while url:
                pages += 1
                if pages % 10 == 0:
                    print(f"  ... fetched {pages} pages of history for {folder} ...")
                    
                response = await client.get(url, headers=headers, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    
                    if "@odata.nextLink" in data:
                        url = data["@odata.nextLink"]
                    elif "@odata.deltaLink" in data:
                        delta_link = data["@odata.deltaLink"]
                        
                        # Save the new delta token
                        sync_token = db.query(SyncToken).filter(SyncToken.folder == folder).first()
                        if not sync_token:
                            sync_token = SyncToken(folder=folder, delta_token=delta_link)
                            db.add(sync_token)
                        else:
                            sync_token.delta_token = delta_link
                            
                        db.commit()
                        print(f"SUCCESS: Captured Delta Token for {folder}! (Took {pages} pages)")
                        break
                    else:
                        print("Error: No nextLink or deltaLink found.")
                        break
                else:
                    print(f"Graph API Error fetching from {folder}: {response.status_code} - {response.text}")
                    break
    except Exception as e:
        print(f"Exception connecting to Graph API for {folder}: {e}")
    finally:
        db.close()

async def run():
    print("Starting Delta Token Initialization...")
    await initialize_delta_token("inbox")
    await initialize_delta_token("sentitems")
    print("Initialization Complete! The background worker will now use these tokens for hyper-fast syncing.")

if __name__ == "__main__":
    asyncio.run(run())
