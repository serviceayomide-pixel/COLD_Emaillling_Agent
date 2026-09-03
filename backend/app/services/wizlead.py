import httpx
from typing import Optional, Dict
from app.core.config import settings

async def find_contact(first_name: str, last_name: str, domain: str) -> Optional[Dict]:
    """
    Calls Wizleads.io API to find an email for a given person and company website.
    Returns a dictionary with contact details (e.g., {'email': 'john@example.com', 'provider': 'Google'}) or None.
    """
    url = "https://api.wizleads.io/email/find-email"
    headers = {
        "x-api-key": settings.WIZLEAD_API_KEY
    }
    params = {
        "first_name": first_name,
        "last_name": last_name,
        "website": domain
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=15.0)
            if response.status_code == 200:
                data = response.json()
                if data.get("email"):
                    return {
                        "first_name": data.get("normalized_fname", first_name),
                        "last_name": data.get("normalized_lname", last_name),
                        "email": data["email"],
                        "provider": data.get("provider", ""),
                        "catchall": data.get("catchall", "")
                    }
            return None
    except Exception as e:
        print(f"Error enriching {first_name} {last_name} at {domain} via Wizlead: {e}")
        return None
