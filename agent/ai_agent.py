import os
import json
from google import genai
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash"


def diagnose_with_ai(checkout):
    prompt = f"""
You are an AI revenue recovery agent.

Analyze this abandoned checkout and identify:
1. The likely payment problem
2. Whether the payment is recoverable
3. The best recovery action
4. A confidence score between 0 and 1
5. A short reason

Checkout:
{json.dumps(checkout, indent=2)}

Return ONLY valid JSON in this format:
{{
    "diagnosis": "short diagnosis",
    "recoverable": true,
    "action": "send_instant_retry_link",
    "confidence": 0.85,
    "reason": "short explanation"
}}

Allowed actions:
- send_instant_retry_link
- send_corrected_payment_link
- schedule_delayed_reminder
- human_review
- skip
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        text = response.text.strip()

        # Remove markdown code fences if Gemini adds them
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except Exception:
        return {
            "available": False,
            "diagnosis": "",
            "recoverable": False,
            "action": "",
            "confidence": 0.0,
            "reason": ""
        }