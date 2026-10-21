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
            transcript_snippet = f"Transcript Auszug: {t[:200]}" if t and t != "No transcript available." else "Kein Transkript verfuegbar"
            video_details.append(
                f"- Video Titel: {v.get('title')}\n"
                f"  Veroeffentlicht: {v.get('published_at')}\n"
                f"  Beschreibung: {v.get('description', '')[:150]}\n"
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
    
    # Conditional greeting rule based on whether we have a name
    has_name = bool(contact_name and contact_name.strip())
    
    if has_name:
        greeting_instruction = f'- MUST start with a personalized greeting using the recipient\'s name (e.g., "Hallo {contact_name},").'
        email2_greeting = f"Hallo {contact_name},"
    else:
        greeting_instruction = '- MUST start with a natural, polite general business greeting since the recipient\'s name is unknown (e.g., "Guten Tag," or "Hallo,"). DO NOT invent a name or use placeholders.'
        email2_greeting = "Guten Tag,"

    # Base prompt payload creation
    research_block = f"""
=== TARGET PROSPECT & RESEARCH DATA ===
TARGET COMPANY: {company_name}
DECISION MAKER: {contact_name if has_name else "Unknown (Address them generally)"}{title_info}

[WEBSITE RESEARCH]
{website_context[:2000] if website_context else "Keine Webseite verfuegbar."}

[YOUTUBE CHANNEL AUDIT & RECENT VIDEOS]
{yt_summary}

[LINKEDIN PROFILE DATA]
{li_summary}
=======================================
"""

    # ── Default Starlight Visuals prompt (used when no custom_prompt is set) ──
    DEFAULT_PROMPT = """ROLE & CONTEXT:
You are a senior Business Development Manager for Starlight Visuals, a premium animation studio specializing in industrial product animation, product visualization, technical animation, game cinematics, and 2D & 3D animation.

Your task is to write a personalized cold email sequence of 4 emails in native German to a decision maker at an industrial company in Germany.

==================================================

AVAILABLE DATA PLACEHOLDERS (auto filled by system):

{current_date} : Today's date
{company_name} : Target company name
{contact_name} : Decision maker's name
{job_title} : Decision maker's position
{website_context} : Scraped website text, products, solutions, investor or company presentations
{linkedin_context} : Scraped LinkedIn company page and recent posts (last 6 months)
{news_context} : Recent news, product launches, trade shows attended
{careers_context} : Careers page
{marketing_context} : Marketing materials, product catalogue
{video_context} : Videos on the website

==================================================

PHASE 1: RESEARCH & ANALYSIS (internal, do not output)

Analyze all data above. Never invent information. If something cannot be verified in the data, do not mention it.

Step 1. Find the hook. Identify one verifiable, timely fact: a product launch, award or nomination, trade show appearance, new technology, sustainability or automation initiative, expansion, or a notable product. Use only website, LinkedIn, news, careers or marketing context for this. Never use {video_context} or YouTube content as the hook.

Step 2. Check the timing. Compare every date in the hook with {current_date}.
- If a trade show starts within the next 7 days or is currently running, do NOT build the email around it. The contact will be busy or away. Choose a different hook, or refer to the show only as a past event the contact has just completed.
- If a trade show ended within the last 14 days, you may refer to it as recent.
- If an event is more than a few weeks away, refer to it as upcoming.
- Never describe an event as upcoming if it has passed, or as past if it has not happened yet.

Step 3. Audit their current visual content. Using {video_context}, {website_context} and {marketing_context}, classify the company into exactly one case:

Case A: Strong visuals. They already have product films, animations or high quality renderings. Acknowledge this briefly and position the gap around what those materials cannot show (internal mechanisms, process sequences, automation, system integration, the product in its application context).

Case B: Mixed visuals. They have some video (e.g. a header loop, a trade show clip, a short product film) but most products are shown only through photos or brochures. Acknowledge what exists and point out that coverage across the portfolio is uneven, for example that the selected product is presented only through photos or a data sheet.

Case C: Static only. They have only photos, CAD images, brochures or catalogues, and no product video or animation in the data. Build the gap around the limits of static material for this specific product: internal function, sequence of operation, scale, interaction of components, or how the product fits into a customer's production line. Do not criticize their existing materials. Frame static material as solid for specification and documentation, but limited for explaining how the product works and creates value.

Case D: Unclear. If the data is insufficient to tell, do not claim anything about their visual content. Write the gap around the product's complexity and the general communication challenge, without referring to what they currently have or lack.

Only classify as Case C if the data clearly supports it. Absence of video in the scraped data is not proof that none exists. When in doubt, use Case D.

Step 4. Select one specific product or product line. Choose the product that is most complex, most innovative, or most closely tied to the hook, and name it in the email. The storyboard offer must refer to this product. Never use a generic phrase like "eines Ihrer Produkte" when a specific product is available. In Case B and Case C, prefer a product that is currently shown only through photos or brochures. Use this same product in all 4 emails.

Step 5. Check the logic. Before writing, confirm that the connection between the hook and the business gap is genuinely valid. Do not claim a trade show appearance or award proves that a product needs explaining. Only state conclusions the evidence supports. If the link is weak, choose a different hook.

==================================================

PHASE 2: EMAIL 1 STRUCTURE (max 200 words, 4 paragraphs plus greeting)

Opening Greeting: Begin with a formal German greeting on its own line, e.g. "Sehr geehrte Frau {contact_name}," or "Sehr geehrter Herr {contact_name},". Use the surname. If gender cannot be determined with confidence from the available data, use "Guten Tag {contact_name}," instead of guessing.

Paragraph 1 (Proof of Research): Open with the verified hook from Step 2. Never open with "Ich hoffe, es geht Ihnen gut" and never introduce yourself first. State the fact, then draw one cautious, logically sound observation from it. Do not compliment without evidence.

Paragraph 2 (The Business Gap): Write this according to the case from Step 3. Never state or imply that the company has no videos unless Case C is clearly supported. In Case C, refer to the specific product and its brochure or photo presentation, and explain what a customer cannot see from it (for example the working sequence, internal components or integration into a line). Then connect this to business outcomes: faster sales conversations, better product understanding, stronger trade show presentations, better customer education, clearer communication with international customers, more efficient marketing. Do not immediately sell animation. Mention international subsidiaries or markets only if confirmed in the data.

Paragraph 3 (Introduce Starlight Visuals): Introduce Starlight Visuals in two sentences. Mention what is relevant to this company from: industrial product animation, technical animation, product visualization, mechanical animation, manufacturing animation, photorealistic CGI, marketing animations. Do not exaggerate or make unrealistic claims.

Paragraph 4 (Value Offer and Soft CTA, combined): Offer a complimentary storyboard concept for the specific product selected in Step 4. Briefly state what it would demonstrate and for which uses (choose two or three that fit the company: website, trade shows, sales presentations, investor presentations, product launches, digital marketing). In Case C, state that the concept would build on the product's existing brochure or photo material, so the company can see what it would look like in motion without having to supply anything new. State clearly that there is no obligation. Then close with one soft call to action in the same paragraph. Do not repeat the offer. Never pressure the reader. Example closings: "Wären Sie offen, sich ein solches Konzept einmal anzusehen?" or "Falls das für Sie interessant klingt, melde ich mich gerne mit einem ersten Entwurf."

==================================================

PHASE 3: THE 4 STEP SEQUENCE

The AI must generate all 4 emails for the sequence, each beginning with the Opening Greeting described in Phase 2 (same salutation in every email).

Email 1: The initial personalized pitch described in Phase 2 (max 200 words).

Email 2: Follow up 1 (max 70 words). A short, polite bump checking whether they had a moment to review the idea for their specific product. Name the product. Do not repeat the pitch or the hook from Email 1.

Email 3: Follow up 2 (max 130 words). A fresh angle on the same product, highlighting visual trade show or sales advantages. Use a different argument than in Email 1. If the Step 2 timing check allows it, a trade show angle may be used. Otherwise focus on sales advantages, such as shorter explanation time in customer conversations, consistent product presentation across sales staff, or easier communication with international customers (only if confirmed in the data).

Email 4: Follow up 3 (max 80 words). A final short check in offering the storyboard before stepping back. Friendly and respectful, no pressure, no fake urgency, no guilt tone. Make clear that the offer stands if the topic becomes relevant later.

Across the sequence, each email must add something new or be shorter and lighter than the one before. Never copy sentences from an earlier email.

==================================================

WRITING STYLE

Write like an experienced German B2B consultant: professional, consultative, research driven, executive level, personal, confident, helpful. Never sound like a marketing agency, a freelancer, or a generic sales template. Never use buzzwords, hype, excessive compliments, marketing clichés, fake urgency, or emojis. Every compliment must be backed by evidence from the data.

Language: Entirely native German business language. It must read as if written by a German professional, not translated from English. A Geschäftsführer oder Marketing Manager must be able to read each email in under one minute.

==================================================

HARD RULES (apply to all 4 emails)

1. Native, executive German business language (no translated English phrases). Also Add subject lines that is engaging and derive from the email content 
2. Word limits: Email 1 max 200 words, Email 2 max 70, Email 3 max 130, Email 4 max 80, including greeting.
3. Do NOT use hyphens or dashes of any kind in the copy. This includes product names, model numbers and compound words. Rewrite compounds as one word (e.g. "Hochleistungsbandsäge"), use spaces, or refer to the product by a descriptive name instead of a model number that contains a hyphen.
4. Every email must open with a professional greeting as described in Phase 2.
5. No email signatures, contact details, sender name, or placeholders at the bottom.
6. No unverifiable claims, no invented statistics, no invented client names.
7. Do not mention that research, scraping or automated tools were used.
8. Never claim or imply that a company lacks video or animation unless Step 3 clearly classifies it as Case C.

==================================================

OUTPUT FORMAT

Output only the 4 final German emails. Separate them with a plain label line: EMAIL 1, EMAIL 2, EMAIL 3, EMAIL 4. Under each label, start directly with the greeting and end with the last sentence of the email, no explanations, no notes, no other headings, no English text.

==================================================

GOAL

The recipient should finish the sequence thinking "They have clearly researched our company, and they understand what we already do" instead of "This is another mass cold email.""""

    # If no custom prompt is set, use the default Starlight Visuals prompt
    if not (custom_prompt and custom_prompt.strip()):
        custom_prompt = DEFAULT_PROMPT

    # Process the prompt (custom or default) with placeholder replacements
    from datetime import datetime
    now_date_str = datetime.now().strftime("%Y-%m-%d")
    user_prompt = custom_prompt.replace("{contact_name}", contact_name) \
                               .replace("{company_name}", company_name) \
                               .replace("{job_title}", title_info) \
                               .replace("{website_context}", website_context[:2000] if website_context else "Keine Webseite verfuegbar.") \
                               .replace("{youtube_context}", yt_summary) \
                               .replace("{video_context}", yt_summary) \
                               .replace("{linkedin_context}", li_summary) \
                               .replace("{current_date}", now_date_str) \
                               .replace("{news_context}", "Keine separaten News-Daten vorhanden.") \
                               .replace("{careers_context}", "Keine separaten Karriereseite-Daten vorhanden.") \
                               .replace("{marketing_context}", "Keine separaten Marketingmaterialien vorhanden.")
    
    # If the prompt didn't include research placeholders, prepend the research block
    # so the LLM ALWAYS has full access to the company's website, YouTube channel, and transcripts!
    if company_name not in user_prompt or yt_summary not in user_prompt:
        base_prompt = f"{research_block}\n\nCOPYWRITING GUIDELINES:\n{user_prompt}"
    else:
        base_prompt = user_prompt



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
        "model": "~anthropic/claude-haiku-latest",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2500,
        "reasoning": {"effort": "none"}
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=90.0)
            if response.status_code == 200:
                data = response.json()
                choices = data.get("choices")
                if choices and len(choices) > 0 and choices[0].get("message", {}).get("content"):
                    content = choices[0]["message"]["content"].strip()
                    
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
                    for key in ["email_1", "email_2", "email_3", "email_4"]:
                        if key in parsed:
                            if "subject" in parsed[key]:
                                parsed[key]["subject"] = strip_hyphens_and_dashes(parsed[key]["subject"])
                            if "body" in parsed[key]:
                                parsed[key]["body"] = strip_hyphens_and_dashes(parsed[key]["body"])
                    
                    return parsed
                else:
                    logger.error(f"OpenRouter response missing content: {data}")
            else:
                logger.error(f"OpenRouter API Error: {response.status_code} - {response.text}")
                
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
