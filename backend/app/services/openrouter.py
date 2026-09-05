import httpx
import json
import logging
import re
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

def strip_hyphens_and_dashes(text: str) -> str:
    """
    Strict post-processing to guarantee zero hyphens or dashes in the final output.
    Replaces hyphens and dashes with spaces or natural rephrasing where needed.
    """
    if not text:
        return text
    # Replace en-dash, em-dash, minus, hyphen with space or remove
    # Characters: - (hyphen-minus), – (en dash), — (em dash), ‐ (hyphen), − (minus sign)
    cleaned = re.sub(r'[\u2010-\u2015\u2212\-]', ' ', text)
    # Collapse multiple spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    return cleaned.strip()

async def generate_email_sequence(
    contact_name: str,
    company_name: str,
    website_context: str,
    youtube_context: Optional[Dict[str, Any]] = None,
    job_title: Optional[str] = None
) -> Optional[Dict]:
    """
    Generates a 2-part hyper-personalized cold outreach sequence in native German for German Industrial,
    Engineering, Manufacturing and Technology companies pitching Technical Visual Storytelling / 3D Animation.
    
    Adheres strictly to the user's Master Prompt specifications:
    - Native, nuanced, non-promotional German
    - Absolutely ZERO hyphens or dashes anywhere in subject or body
    - Deep website & product analysis
    - Deep YouTube audit & video analysis
    - Low-friction, value-driven CTA
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://frontend-production-cc0b.up.railway.app",
        "X-Title": "Client Acquisition AI - German B2B Engine",
        "Content-Type": "application/json"
    }

    # Format YouTube data for the prompt
    yt_summary = "Keine offiziellen YouTube Daten vorhanden."
    if youtube_context and not youtube_context.get("error"):
        stats = youtube_context.get("stats", {})
        videos = youtube_context.get("recent_videos", [])
        video_details = []
        for v in videos:
            t = v.get('transcript')
            transcript_snippet = f"Transcript Auszug: {t[:400]}" if t and t != "No transcript available." else "Kein Transkript verfuegbar"
            video_details.append(
                f"- Video Titel: {v.get('title')}\n"
                f"  Veroeffentlicht: {v.get('published_at')}\n"
                f"  Beschreibung: {v.get('description', '')[:300]}\n"
                f"  {transcript_snippet}"
            )
        videos_str = "\n".join(video_details) if video_details else "Keine aktuellen Videos gefunden."
        yt_summary = (
            f"Kanal Titel: {stats.get('title', 'Unbekannt')}\n"
            f"Abonnenten: {stats.get('subscriber_count', 'Unbekannt')}, Videoanzahl: {stats.get('video_count', 'Unbekannt')}\n"
            f"Aktuelle Videos:\n{videos_str}"
        )

    title_info = f" ({job_title})" if job_title else ""

    prompt = f"""
MASTER PROMPT
Hyper Personalized B2B Cold Email for German Industrial, Engineering, Manufacturing and Technology Companies

ROLE
Act as one of the world's best B2B enterprise cold email copywriters and research driven outbound strategists specializing in:
Industrial manufacturing, Engineering, Automation, Robotics, Machinery, Renewable energy, Semiconductor technology, Process technology, Industrial software, SaaS, Technical products, Engineering services, Production technology, Energy technology, Water technology, Advanced manufacturing.

RECIPIENT
Name: {contact_name}{title_info}
Company: {company_name}
Target Personas: Marketing Directors, Heads of Marketing, Leiter Marketing, Leiter Marketing und Kommunikation, Head of Marketing & Communications, Managing Directors.

CORE OBJECTIVE & POSITIONING
The objective is NOT to simply sell "3D animation".
The objective is to identify where the company's existing technical communication could become clearer, more engaging and easier to understand, then position technical visual storytelling as an additional communication layer that can help the company explain complex products, technologies, processes and engineering value.
You are essentially proposing:
"You already have the technical expertise and content. We can add a visual storytelling layer that makes the value easier to understand."

LANGUAGE REQUIREMENT
The final outreach emails MUST be written in natural, native German.
Do not translate English word for word.
Write the way a strong German B2B marketing professional would actually write to another German business professional.
The language should feel: Professional, Natural, Confident, Concise, Human, Specific, Business focused, Non promotional, Non robotic.
Avoid exaggerated sales language and American style sales expressions.
Avoid generic phrases such as "Ich hoffe, diese Nachricht erreicht Sie gut", "Ich wollte mich kurz vorstellen", "Wir sind eine fuehrende Animationsagentur".

CRITICAL FORMATTING RULE (ABSOLUTE)
DO NOT USE ANY HYPHENS OR DASHES IN THE FINAL EMAIL OUTPUT.
Zero hyphens. Zero en dashes. Zero em dashes. Zero dash bullet points.
Rewrite sentences naturally so that hyphens and dash characters are completely unnecessary.
Example: instead of "End to End", write "von Anfang bis Ende". Instead of "3D Animation", write "3D Visualisierung" or "Raeumliche Animation" without dashes. Instead of "60 bis 90 Sekunden", write "in einer Minute" or "innerhalb weniger Augenblicke".

RESEARCH DATA PROVIDED FOR THIS COMPANY:
[COMPANY WEBSITE CONTEXT]
{website_context[:4500]}

[YOUTUBE CHANNEL AUDIT DATA]
{yt_summary}

EMAIL 1 (DAY 1 - INITIAL OUTREACH) REQUIREMENTS:
1. Conduct research based on the provided website and YouTube data.
2. Structure:
   - Paragraph 1: Specific observation about the company's product, technology, or current communication.
   - Paragraph 2: Communication insight (what live video or text shows vs what remains invisible like internal mechanics, fluid dynamics, flow of energy or data).
   - Paragraph 3: Visual opportunity (position visual storytelling as an additional layer, not a replacement).
   - Paragraph 4: Concrete visualization idea for one specific product or technology of {company_name}.
   - Paragraph 5: Low friction CTA (e.g. "Wenn das grundsaetzlich interessant ist, kann ich Ihnen gern einmal skizzieren, wie ich das fuer [Produkt] visuell aufbauen wuerde.").
3. Tone: Respectful, observant, professional, no hype, no hard sales pitch.

EMAIL 2 (DAY 3 - FOLLOW UP TOUCH) REQUIREMENTS:
1. Follow the "I took another look" principle (Der zweite Blick).
2. Do NOT say "Just following up", "Ich wollte nachfassen", or apologize for following up.
3. Keep it shorter (around 60 to 110 words in German).
4. Introduce a second angle or deepen the first thought (e.g. focusing on a specific internal process, trade fair / sales enablement use case, or cross section cutaway).
5. Very low friction CTA (e.g. offering a quick storyboard or visual sketch with no call required).
6. Must also strictly contain ZERO hyphens or dashes.

OUTPUT FORMAT:
Return ONLY a valid, raw JSON object (no markdown backticks, no explanatory text outside the JSON) with the following exact keys:
{{
  "email_1": {{
    "subject": "Kurzer praeziser Betreff ohne Bindestriche",
    "body": "Vollstaendiger deutscher Emailtext ohne jegliche Bindestriche oder Gedankenstriche\\n\\nBeste Gruesse\\n{settings.SENDER_NAME}\\n{settings.COMPANY_NAME}"
  }},
  "email_2": {{
    "subject": "Neuer Betreff fuer den Follow up ohne Bindestriche",
    "body": "Vollstaendiger deutscher Follow up Text ohne jegliche Bindestriche oder Gedankenstriche\\n\\nBeste Gruesse\\n{settings.SENDER_NAME}\\n{settings.COMPANY_NAME}"
  }}
}}
"""

    payload = {
        # Using Claude 3.5 Sonnet for master-level prompt following and strict negative constraint adherence
        "model": "anthropic/claude-3.5-sonnet",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=90.0)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                # Strip markdown blocks if present
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                
                parsed = json.loads(content.strip())
                
                # Apply strict programmatic sanitation to guarantee ZERO hyphens or dashes in subjects and bodies
                for key in ["email_1", "email_2"]:
                    if key in parsed:
                        if "subject" in parsed[key]:
                            parsed[key]["subject"] = strip_hyphens_and_dashes(parsed[key]["subject"])
                        if "body" in parsed[key]:
                            parsed[key]["body"] = strip_hyphens_and_dashes(parsed[key]["body"])
                
                return parsed
            else:
                logger.error(f"OpenRouter API Error: {response.status_code} - {response.text}")
                # Fallback to Claude 3 Haiku if Sonnet experiences an issue
                fallback_payload = dict(payload)
                fallback_payload["model"] = "anthropic/claude-3-haiku"
                fb_response = await client.post(url, json=fallback_payload, headers=headers, timeout=45.0)
                if fb_response.status_code == 200:
                    fb_data = fb_response.json()
                    fb_content = fb_data["choices"][0]["message"]["content"].strip()
                    if fb_content.startswith("```json"): fb_content = fb_content[7:]
                    elif fb_content.startswith("```"): fb_content = fb_content[3:]
                    if fb_content.endswith("```"): fb_content = fb_content[:-3]
                    parsed = json.loads(fb_content.strip())
                    for key in ["email_1", "email_2"]:
                        if key in parsed:
                            if "subject" in parsed[key]:
                                parsed[key]["subject"] = strip_hyphens_and_dashes(parsed[key]["subject"])
                            if "body" in parsed[key]:
                                parsed[key]["body"] = strip_hyphens_and_dashes(parsed[key]["body"])
                    return parsed
                return None
    except Exception as e:
        logger.error(f"Error generating German email sequence for {contact_name} at {company_name}: {e}")
        return None

async def analyze_reply_intent(email_body: str) -> str:
    """Uses Claude to classify the intent of a reply in German or English."""
    prompt = f"""You are analyzing an email reply from a German or international business prospect who received a B2B cold email regarding technical visual storytelling and 3D visualization.
IMPORTANT: Ignore any email signature, disclaimer, or quoted email history/previous messages in the thread. Only analyze the actual new reply text written by the sender.

Read the prospect's email reply and classify their intent into exactly ONE of the following categories:
- Booked (They have booked a call or accepted an appointment)
- Interested (They want to see a visual concept, asked for a sketch/storyboard, asked for more information, portfolio, pricing, or said "gerne zeigen", "senden Sie mir das zu", "klingt interessant")
- Not Interested (They said no, kein Interesse, stop emailing, unsubscribe, or no thanks)
- Out of Office (Auto-reply indicating absence / Abwesenheitsnotiz)
- Wrong Contact (They said they are not the right person, or referred to another colleague like Leiter Marketing)

Prospect's Email Reply:
"{email_body}"

Output ONLY the category name. No other text."""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=15.0
            )
            data = response.json()
            intent = data['choices'][0]['message']['content'].strip()
            valid_intents = ["Not Interested", "Booked", "Interested", "Out of Office", "Wrong Contact"]
            for v in valid_intents:
                if v.lower() in intent.lower():
                    return v
            return "Unknown"
    except Exception as e:
        logger.error(f"Error classifying reply: {e}")
        return "Unknown"
