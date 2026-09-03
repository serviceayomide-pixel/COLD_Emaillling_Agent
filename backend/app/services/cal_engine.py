import httpx
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from app.core.config import settings

# Cal.com API Base URL
CAL_API_URL = "https://api.cal.com/v2"

async def fetch_available_slots(date_from: str, date_to: str, event_type_id: int = 6154180) -> List[str]:
    """
    Ping Cal.com Developer API (v2) to find available slots for a given date range.
    """
    print(f"[Cal.com Engine] Fetching slots from {date_from} to {date_to}...")
    
    if not settings.CAL_API_KEY:
        print("[Cal.com Engine] Warning: CAL_API_KEY is not set. Returning empty slots.")
        return []

    available_slots = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{CAL_API_URL}/slots/available",
                params={
                    "eventTypeId": event_type_id,
                    "startTime": date_from,
                    "endTime": date_to
                },
                headers={
                    "Authorization": f"Bearer {settings.CAL_API_KEY}",
                    "cal-api-version": "2024-08-13"
                },
                timeout=10.0
            )
            
            if resp.status_code != 200:
                print(f"[Cal.com Engine] Failed to fetch slots: {resp.status_code} {resp.text}")
                return []
                
            resp_data = resp.json()
            
            # v2 returns {"status": "success", "data": {"slots": {"2026-06-30": [{"time": "2026-06-30T10:00:00.000Z"}...]}}}
            if "data" in resp_data and "slots" in resp_data["data"]:
                slots_data = resp_data["data"]["slots"]
            elif "slots" in resp_data:
                slots_data = resp_data["slots"]
            else:
                slots_data = {}
            
            # Extract times from the grouped dictionary
            for date_key, daily_slots in slots_data.items():
                for slot in daily_slots:
                    if "time" in slot:
                        available_slots.append(slot["time"])
                        
    except Exception as e:
        print(f"[Cal.com Engine] Failed to fetch slots: {e}")
    
    return sorted(available_slots)


async def book_meeting(email: str, name: str, start_time: str, event_type_id: int = 6154180) -> Dict:
    """
    Ping Cal.com Developer API (v2) to instantly book a meeting.
    """
    print(f"[Cal.com Engine] Booking meeting for {name} ({email}) at {start_time}...")
    
    if not settings.CAL_API_KEY:
        raise ValueError("CAL_API_KEY is missing")

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{CAL_API_URL}/bookings",
                headers={
                    "Authorization": f"Bearer {settings.CAL_API_KEY}",
                    "cal-api-version": "2024-08-13"
                },
                json={
                    "eventTypeId": event_type_id,
                    "start": start_time,
                    "attendee": {
                        "name": name,
                        "email": email,
                        "timeZone": "Europe/London"
                    }
                },
                timeout=15.0
            )
            
            if resp.status_code not in [200, 201]:
                print(f"[Cal.com Engine] Booking failed: {resp.text}")
                return {"status": "FAILED", "reason": resp.text}
                
            resp_data = resp.json()
            data = resp_data.get("data", resp_data.get("booking", {}))
            
            return {
                "status": "SUCCESS",
                "booking_id": data.get("id"),
                "meeting_link": f"https://cal.com/booking/{data.get('uid')}",
                "attendee": {
                    "name": name,
                    "email": email
                },
                "start_time": start_time
            }
            
    except Exception as e:
        print(f"[Cal.com Engine] Exception during booking: {e}")
        return {"status": "FAILED", "reason": str(e)}
