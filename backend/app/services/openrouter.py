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
    cleaned = re.sub(r'[\u2010-\u2015\u2212\-]', ' ', text)
    # Collapse multiple spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    return cleaned.strip()

async def generate_email_sequence(
    contact_name: str,
    company_name: str,
    website_context: str,
    youtube_context: Optional[Dict[str, Any]] = None,
    linkedin_context: Optional[Dict[str, Any]] = None,
    job_title: Optional[str] = None,
    custom_prompt: Optional[str] = None
) -> Optional[Dict]:
    """
    Generates a 2-part hyper-personalized cold outreach sequence in native German.
    Uses Claude Sonnet via OpenRouter. Falls back to Claude 3.5 Sonnet on error.
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

    # Format LinkedIn data for the prompt
    li_summary = "Keine LinkedIn Profildaten vorhanden."
    if linkedin_context:
        parts = []
        if linkedin_context.get("headline"):
            parts.append(f"Headline: {linkedin_context['headline']}")
        if linkedin_context.get("about"):
            parts.append(f"Ueber mich: {linkedin_context['about'][:500]}")
        if linkedin_context.get("current_company"):
            parts.append(f"Aktuelles Unternehmen: {linkedin_context['current_company']}")
        if linkedin_context.get("experience"):
            parts.append(f"Erfahrung: {linkedin_context['experience']}")
        if linkedin_context.get("recent_posts"):
            parts.append(f"Aktuelle Posts:\n{linkedin_context['recent_posts'][:600]}")
        if parts:
            li_summary = "\n".join(parts)

    title_info = f" ({job_title})" if job_title else ""

    # Base prompt payload creation
    if custom_prompt and custom_prompt.strip():
        # Using the user's custom prompt from the dashboard
        base_prompt = custom_prompt.replace("{contact_name}", contact_name) \
                                   .replace("{company_name}", company_name) \
                                   .replace("{job_title}", title_info) \
                                   .replace("{website_context}", website_context[:4500] if website_context else "Keine Webseite verfuegbar.") \
                                   .replace("{youtube_context}", yt_summary) \
                                   .replace("{linkedin_context}", li_summary)
    else:
        # User's Updated Master Prompt
        base_prompt = f"""
ROLE
You are a senior B2B outreach strategist and copywriter specializing in 3D animation and visual storytelling for technical and industrial companies. Your pitch covers two things animation does for a company like this: making invisible internal processes understandable, and presenting the products themselves (their design, assembly, configurations, and use in context) more compellingly than static photos and text ever could. Your job is to research a target company deeply enough to write one cold email that reads as if it came from someone who has genuinely studied their business — not a templated pitch.

VARIABLES:
- COMPANY_NAME: {company_name}
- DECISION_MAKER_NAME: {contact_name}
- DECISION_MAKER_ROLE: {title_info if title_info else "Marketing Manager"}
- LANGUAGE: German

RESEARCH DATA PROVIDED FOR THIS COMPANY:
[COMPANY WEBSITE CONTEXT]
{website_context[:4500] if website_context else "Keine Webseite verfuegbar."}

[YOUTUBE CHANNEL AUDIT DATA]
{yt_summary}

[LINKEDIN PROFILE DATA]
{li_summary}

PHASE 1 — RESEARCH (do this before writing anything)
1. Identify the full breadth of the company’s product/solution portfolio.
2. Note what's on their YouTube (is video already a priority?).
3. Check the decision maker's LinkedIn profile data if provided. Pull ONE genuine, professional detail to use for personalization if it surfaces. Stay strictly professional.
4. Identify one flagship product or platform to use as a case study. Prioritize a product that fits either: 
   - Invisible mechanism (internal fluid/thermal cycling, sub-micron alignment).
   - Product presentation (complex, modular, hard to convey).
   Use concrete specifics (tolerances, stages, options).
5. Tailor the research emphasis to the decision maker’s specific role.
6. Note where the company appears in public trade contexts.

PHASE 2 — CHOOSE THE PERSONA-SPECIFIC VALUE FRAME
- CEO/President: Animation as a strategic differentiator that shortens sales cycles.
- Managing Director: Animation as a way to compete locally.
- Founder: Animation as a way to tell the founding story and real engineering.
- Marketing Manager/Comms: Animation as a marketing asset that outperforms static collateral.

PHASE 3 — WRITE THE EMAIL (EMAIL 1)
Structure (5 short paragraphs, no more):
1. Proof of research (name 2-3 distinct product lines). Weave in a genuine personal detail if found.
2. The gap: Technical depth is explained mostly through text/datasheets, or products shown through flat photos.
3. The case study: Pick ONE flagship product and go deep on the angle (invisible internal process or complex presentation). Show you understand their engineering.
4. Zoom out to the portfolio: The same approach applies across their other solution areas.
5. The ask: Invite them to collaborate, offer to prepare a storyboard for the case-study product's animation and go through it together. No call/meeting request.

Hard rules for Email 1:
- Write entirely in German.
- NO hyphens or dashes anywhere in the body copy. Rewrite around them.
- No generic filler phrases ("I hope this email finds you well").
- Every specific technical claim must come from the research.
- Do not write a sign off or signature block (no name, company, or phone number). End the email on the final sentence of the ask.

PHASE 4 — OUTPUT
You must output exactly 4 emails in a strict JSON format.

EMAIL 2 (FOLLOW-UP 1) STRICT RULE:
For Email 2, you MUST NOT write a custom email. You MUST use exactly this template, translated to German, and fill in the [Name] and [the case study product] to EXACTLY MATCH what you used in Email 1:
"Hallo [Name],
wollte nur kurz nachfragen bezueglich meiner Nachricht von vor ein paar Tagen ueber [the case study product]. Passte das zeitlich gerade gut fuer einen kurzen Blick?
Ich bin gespannt auf Ihre Gedanken und sende Ihnen bei Interesse gern das Storyboard Beispiel zu."
(Do NOT add a signature block at the end).

EMAIL 3 (FOLLOW-UP 2) STRICT RULE:
This email should restate the core pitch and context of Email 1. It must focus on the EXACT same [the case study product] and the same core problem (invisible mechanisms or complex presentation), but conveyed using slightly different words. It should read as a fresh attempt to explain the value of 3D animation for that specific product.
(Do NOT add a signature block at the end).

EMAIL 4 (FOLLOW-UP 3) STRICT RULE:
This is the final bump. It should have the exact same meaning and intent as Email 2 (checking in to see if they had time to read about the case study product and offering the storyboard), but written using different words so it doesn't look copy-pasted. Keep it short and punchy.
(Do NOT add a signature block at the end).
"""

    json_lock = f"""
OUTPUT FORMAT (STRICT):
Return ONLY a valid, raw JSON object (no markdown backticks, no explanatory text outside the JSON) with the exact keys below.
CRITICAL JSON RULE: You MUST escape any double quotes inside the email body using a backslash (e.g., \\"Beispiel\\") otherwise the JSON will break!
{{
  "email_1": {{
    "subject": "Kurzer praeziser Betreff ohne Bindestriche",
    "body": "Vollstaendiger deutscher Emailtext nach den Strukturvorgaben (Keine Signatur am Ende)"
  }},
  "email_2": {{
    "subject": "Kurzer Betreff fuer den Follow up",
    "body": "Exakt die vorgegebene Follow-up Vorlage, bei der [Name] und [the case study product] ausgefuellt sind (Keine Signatur am Ende)"
  }},
  "email_3": {{
    "subject": "Neuer Betreff fuer die zweite Follow-up Mail",
    "body": "Neu geschriebener Pitch fuer das gleiche Produkt wie in Email 1 (Keine Signatur am Ende)"
  }},
  "email_4": {{
    "subject": "Kurzer Betreff fuer den letzten Check-in",
    "body": "Kurze Nachfrage in anderen Worten als Email 2 (Keine Signatur am Ende)"
  }}
}}
"""
    prompt = base_prompt + "\n" + json_lock

    payload = {
        "model": "anthropic/claude-sonnet-4.6",
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
                
                # Sanitize the output to remove invalid control characters before parsing
                sanitized_content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
                parsed = json.loads(sanitized_content.strip(), strict=False)
                
                # Apply strict programmatic sanitation to guarantee ZERO hyphens or dashes
                for key in ["email_1", "email_2"]:
                    if key in parsed:
                        if "subject" in parsed[key]:
                            parsed[key]["subject"] = strip_hyphens_and_dashes(parsed[key]["subject"])
                        if "body" in parsed[key]:
                            parsed[key]["body"] = strip_hyphens_and_dashes(parsed[key]["body"])
                
                return parsed
            else:
                logger.error(f"OpenRouter API Error: {response.status_code} - {response.text}")
                # Fallback to Claude 3.5 Sonnet
                fallback_payload = dict(payload)
                fallback_payload["model"] = "anthropic/claude-3.5-sonnet"
                fb_response = await client.post(url, json=fallback_payload, headers=headers, timeout=90.0)
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


async def classify_auto_reply(subject: str, body: str) -> str:
    """
    Uses GPT-4o-mini to classify whether an incoming email is a real human reply
    or an automatic reply (Out of Office, auto-responder, delivery notification, etc).
    Returns: 'real_reply' or 'auto_reply'
    """
    prompt = f"""You are classifying an incoming email to determine if it was written by a real human or if it is an automated system response.

CLASSIFY as 'auto_reply' if the message is:
- An Out of Office / Abwesenheitsnotiz / Automatische Antwort
- An auto-responder or vacation reply
- A system-generated delivery notification
- A "this mailbox is not monitored" message
- Any automated response not written by a human

CLASSIFY as 'real_reply' if the message is:
- Written by a real person responding to the original email
- Contains original thoughts, questions, or feedback from a human
- Even if short (e.g. "Danke", "Kein Interesse", "Bitte senden Sie mir mehr Informationen")

Email Subject: "{subject}"
Email Body: "{body[:500]}"

Output ONLY one of these two words: real_reply or auto_reply"""

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",
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
                timeout=10.0
            )
            data = response.json()
            result = data['choices'][0]['message']['content'].strip().lower()
            if "auto_reply" in result:
                return "auto_reply"
            return "real_reply"
    except Exception as e:
        logger.error(f"Error classifying auto-reply: {e}")
        # Default to real_reply to be safe (stops the sequence)
        return "real_reply"


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
