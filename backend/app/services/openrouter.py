import httpx
import json
from typing import Optional, Dict
from app.core.config import settings

async def generate_email_sequence(contact_name: str, company_name: str, context: str) -> Optional[Dict]:
    """
    Uses OpenRouter (Claude/GPT) to generate a 4-part personalized email sequence.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:3000", # Required by OpenRouter
        "X-Title": "Client Acquisition AI", # Required by OpenRouter
        "Content-Type": "application/json"
    }

    prompt = f"""
    You are an elite B2B cold email copywriter.
    You are writing a 4-part cold email sequence to {contact_name} at {company_name}.
    
    Here is the scraped context about their company:
    {context}
    
    Rules for the emails:
    1. Make them sound highly personalized and human.
    2. The core offer is: We help UK care providers improve how they generate enquiries online (better websites, landing pages, automated follow-up systems).
    3. The benefits to highlight: More private care enquiries, faster response to new leads, better online credibility, less manual admin.
    4. Call to Action: Would you be open to a quick 15-minute call next week to see if this could help {company_name}?
    5. Always sign off EXACTLY with:
       Kind regards,
       {settings.SENDER_NAME}
       {settings.COMPANY_NAME}
       
       (Reply STOP to opt out)
       
    6. Email 1 (Day 1): Initial pitch mentioning something specific about their company based on the scraped context, tying it into the core offer and benefits.
    7. Email 2 (Day 3): A short follow-up in case they missed the first email, briefly reiterating the core offer. Example: "Just following up in case my earlier email got missed. We’re helping care agencies improve their online enquiry process... Would it be worth a short conversation?"
    8. Email 3 (Day 7): Adding a tiny bit of value or a quick question.
    9. Email 4 (Day 14): The final polite follow-up (breakup email).

    Output EXACTLY a JSON object with this structure:
    {{
      "email_1": {{"subject": "...", "body": "..."}},
      "email_2": {{"subject": "...", "body": "..."}},
      "email_3": {{"subject": "...", "body": "..."}},
      "email_4": {{"subject": "...", "body": "..."}}
    }}
    Do not wrap in markdown blocks, just raw JSON. Do not use HTML tags in the body, just use standard newline characters (\\n).
    """

    payload = {
        # claude-3-haiku is fast, cheap, and reliably outputs JSON when instructed
        "model": "anthropic/claude-3-haiku",
        "messages": [
            {"role": "user", "content": prompt}
        ]
        # NOTE: response_format is NOT used — not all OpenRouter models support it.
        # Instead, the prompt explicitly instructs the model to return raw JSON.
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=45.0)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # Safely strip markdown backticks if the AI wraps the JSON
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                elif content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                    
                return json.loads(content.strip())
            print(f"OpenRouter API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error generating email for {contact_name} via OpenRouter: {e}")
        return None

async def analyze_reply_intent(email_body: str) -> str:
    """Uses Claude to classify the intent of a reply."""
    prompt = f"""You are analyzing a reply from a prospect for a UK Healthcare Recruitment Agency.
IMPORTANT: Ignore any email signature, disclaimer, or quoted email history/previous messages in the thread. Only analyze the actual new reply text written by the sender.

Read the prospect's email reply and classify their intent into exactly ONE of the following categories:
- Booked (They have booked a call or accepted a calendar invite)
- Interested (They want to book a call, asked for times, asked for more information, brochure, pricing, or said "tell me more" or "send details")
- Not Interested (They said no, stop emailing, unsubscribe, or no thanks)
- Out of Office (Auto-reply indicating they are away)
- Wrong Contact (They said they are not the right person, or gave someone else's email)

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
            # Clean up the output to make sure it matches our categories
            valid_intents = ["Not Interested", "Booked", "Interested", "Out of Office", "Wrong Contact"]
            for v in valid_intents:
                if v.lower() in intent.lower():
                    return v
            return "Unknown"
    except Exception as e:
        print(f"Error classifying reply: {e}")
        return "Unknown"
