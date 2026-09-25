import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

ACTOR_ID = "curious_coder~linkedin-profile-scraper"


async def scrape_linkedin_profile(linkedin_url: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes a LinkedIn profile using the Apify actor.
    Returns structured profile data (headline, about, experience) or None on failure.
    """
    if not linkedin_url:
        return None

    api_key = settings.APIFY_API_KEY
    if not api_key:
        logger.warning("APIFY_API_KEY not configured. Skipping LinkedIn scrape.")
        return None

    # Normalize the URL
    if not linkedin_url.startswith("http"):
        linkedin_url = f"https://{linkedin_url}"

    # Use the synchronous run endpoint to get results in one call
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
    params = {"token": api_key}
    payload = {
        "profileUrls": [linkedin_url]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                params=params,
                json=payload,
                timeout=60.0  # LinkedIn scraping can take a while
            )

            if response.status_code == 200 or response.status_code == 201:
                results = response.json()
                if results and len(results) > 0:
                    profile = results[0]
                    return {
                        "name": profile.get("name", ""),
                        "headline": profile.get("headline", ""),
                        "about": profile.get("about", ""),
                        "location": profile.get("location", ""),
                        "current_company": profile.get("currentCompany", ""),
                        "experience": _format_experience(profile.get("experience", [])),
                        "recent_posts": _format_posts(profile.get("posts", [])),
                    }
                else:
                    logger.warning(f"Apify returned empty results for {linkedin_url}")
                    return None
            else:
                logger.error(f"Apify API Error: {response.status_code} - {response.text[:500]}")
                return None

    except httpx.TimeoutException:
        logger.error(f"Apify request timed out for {linkedin_url}")
        return None
    except Exception as e:
        logger.error(f"Error scraping LinkedIn profile {linkedin_url}: {e}")
        return None


def _format_experience(experience_list: list) -> str:
    """Formats the experience list into a readable string for the prompt."""
    if not experience_list:
        return "Keine Erfahrungsdaten verfuegbar."

    parts = []
    for exp in experience_list[:3]:  # Limit to last 3 positions
        title = exp.get("title", "")
        company = exp.get("company", "")
        duration = exp.get("duration", "")
        parts.append(f"{title} bei {company} ({duration})")

    return "; ".join(parts) if parts else "Keine Erfahrungsdaten verfuegbar."


def _format_posts(posts_list: list) -> str:
    """Formats recent LinkedIn posts into a readable string for the prompt."""
    if not posts_list:
        return "Keine aktuellen LinkedIn Posts gefunden."

    parts = []
    for post in posts_list[:3]:  # Limit to last 3 posts
        text = post.get("text", "")
        if text:
            parts.append(text[:200])  # Truncate long posts

    return "\n".join(parts) if parts else "Keine aktuellen LinkedIn Posts gefunden."
