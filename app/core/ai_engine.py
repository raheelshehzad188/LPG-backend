import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()


def _extract_lead_info(text: str, messages: list) -> dict | None:
    """Try to extract name, phone from conversation."""
    lead = {}
    full_text = " ".join([str(m) for m in messages]) + " " + (text or "")
    phone_match = re.search(r"(\+92\s?\d{2}\s?\d{7}|\d{4}[\s-]?\d{7}|03\d{2}\s?\d{7})", full_text.replace("-", ""))
    if phone_match:
        lead["phone"] = phone_match.group(1).strip()
    name_patterns = [
        r"(?:mera naam|my name is|I am| naam )\s*[: ]?\s*([A-Za-z\s]+?)(?:\.|,|$)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)",
    ]
    for pat in name_patterns:
        m = re.search(pat, full_text, re.I)
        if m:
            lead["name"] = m.group(1).strip()
            break
    return lead if lead else None


async def get_ai_response(query, context_messages, db=None, gemini_settings=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if gemini_settings and gemini_settings.api_key:
        api_key = gemini_settings.api_key
    if not api_key:
        return {"question": "API Key missing in .env file", "listings": [], "message": "", "lead_info": None, "lead_id": None}

    genai.configure(api_key=api_key)
    model_name = (gemini_settings.model if gemini_settings else None) or os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

    system_prompt = "You are 'Lahore Property Guide' AI agent. Help users find plots and houses in Lahore. Keep it professional and helpful. Ek ek question poocho."
    if gemini_settings:
        if gemini_settings.system_instructions:
            system_prompt = gemini_settings.system_instructions
        if gemini_settings.conversation_instructions:
            system_prompt += "\n\n" + gemini_settings.conversation_instructions

    try:
        model = genai.GenerativeModel(model_name=model_name)
        full_prompt = f"{system_prompt}\n\nChat History: {context_messages}\n\nUser Query: {query}"
        response = model.generate_content(full_prompt)

        question = response.text if response and response.text else "AI response empty."
        lead_info = _extract_lead_info(question, context_messages)
        lead_id = None

        if db and lead_info and lead_info.get("name") and lead_info.get("phone"):
            from app.models.lead import Lead
            lead = Lead(
                name=lead_info.get("name"),
                phone=lead_info.get("phone"),
                context=str(context_messages)[:500],
                ai_summary=question[:200],
                source="AI Search",
            )
            db.add(lead)
            db.commit()
            db.refresh(lead)
            lead_id = f"L{lead.id}"
            if lead_info:
                lead_info["lead_id"] = lead_id

        return {
            "question": question,
            "listings": [],
            "message": "",
            "lead_info": lead_info,
            "lead_id": lead_id,
        }
    except Exception as e:
        print(f"❌ AI ENGINE ERROR: {str(e)}")
        return {"question": f"Model Error: {str(e)}", "listings": [], "message": "", "lead_info": None, "lead_id": None}