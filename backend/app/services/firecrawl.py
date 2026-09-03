import httpx
from typing import Optional
from app.core.config import settings

async def scrape_company_context(url: str) -> Optional[str]:
    """
    Scrapes the company website using Firecrawl to get business context.
    Returns markdown text of the site.
    """
    if not url:
        return None

    # Firecrawl v1 endpoint (v0 is deprecated)
    api_url = "https://api.firecrawl.dev/v1/scrape"
    headers = {
        "Authorization": f"Bearer {settings.FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                # Firecrawl v1 returns data -> markdown
                return data.get("data", {}).get("markdown", "")
            print(f"Firecrawl API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error scraping {url} via Firecrawl: {e}")
        return None
