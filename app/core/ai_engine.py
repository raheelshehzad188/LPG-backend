"""
LPG AI Engine — thread-based, lead collection, minimal context for speed.
- threadId = unique chat session
- Chat history stored in DB (chat_messages), only last N sent to Gemini
- Lead create when name+phone; update if thread already has lead
- Context caching: system prompt ek bar cache, har request pe na bhejo
"""
import os
import re
import json
import datetime
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Max messages to send to Gemini (keeps response fast)
MAX_CONTEXT_MESSAGES = 8

# Cache — system prompt 1 bar cache, reuse
# Gemini: min 32k tokens, TTL default 1 hour. Hum 55 min pe proactive re-create karte hain.
_cached_prompt_cache = None
_cached_prompt_expiry = None
CACHE_TTL_MINUTES = int(os.getenv("GEMINI_CACHE_TTL_MINUTES", "60"))  # 1 hour
PROACTIVE_REFRESH_MINUTES = int(os.getenv("GEMINI_CACHE_REFRESH_MINUTES", "55"))  # 5 min pehle refresh
MIN_CACHE_TOKENS = int(os.getenv("GEMINI_MIN_CACHE_TOKENS", "32768"))  # Gemini cache min


def invalidate_gemini_cache(delete_on_api: bool = True):
    """Admin ke instructions update hone par call — purana cache hatake naya banaega.
    delete_on_api=True: Gemini API par se bhi delete try karega."""
    global _cached_prompt_cache, _cached_prompt_expiry
    if _cached_prompt_cache and delete_on_api:
        try:
            _cached_prompt_cache.delete()
        except Exception as e:
            print(f"[LPG] Cache delete skipped: {e}")
    _cached_prompt_cache = None
    _cached_prompt_expiry = None

LEAD_COLLECT_PROMPT = """Tu Lahore Property Guide ka AI assistant ho.

CRITICAL — Reply SHORT rakho:
- Max 1-2 SENTENCES. Zyada mat likho.
- Lists mat banao. Bullet points mat do. Details mat do.
- Sirf seedha jawab ya 1 question.

Order maintain karo:
   Step 1: Kya chahte ho? (plot/house/flat)
   Step 2: Budget kitna? (lac/crore)
   Step 3: Location? (DHA/Bahria)
   Step 4: Naam?
   Step 5: WhatsApp number?
- Ek waqt pe SIRF 1 question. Lists, advice, tips mat do.
- Jab naam+phone mil jaye: reply end mein LEAD_COLLECTED:{"name":"...","phone":"...","budget":"...","interest":"..."}
- Plain text. ```json mat use karo.
- Kabhi 3+ lines mat likho. No ###, no bullets.
- FILTER_CRITERIA: jab user ne bataya ho, reply end: FILTER_CRITERIA:{"area":"DHA","type":"plot","budget_max_lac":500}
"""


def _get_property_data_for_cache(db) -> str:
    """Property data — 32k min ke liye pad kiya jayega. Use this to filter/recommend."""
    try:
        from app.models.property import Property
        rows = db.query(Property).limit(500).all()
        if not rows:
            return _CACHE_FILLER
        lines = []
        for p in rows:
            lines.append(f"{p.location_name or ''} | {p.type or ''} | {p.title or ''} | {float(p.price or 0)/100000:.0f} lac | {p.area_size or ''}")
        return "\n".join(lines) + "\n" + _CACHE_FILLER
    except Exception:
        return _CACHE_FILLER


_CACHE_FILLER = """
Lahore Property Guide — Areas: DHA Phase 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, Prism. Bahria Town, Gulberg, Model Town, Johar, WAPDA Town, Askari, Cavalry.
Types: plot, house, flat, commercial. Prices in lakh (1 lac=100000) and crore (1 cr=100 lac).
Budget examples: 50 lac, 1 crore, 2 crore, 5 crore. Use above data to suggest matching properties.
"""


def _estimate_tokens(text: str) -> int:
    """Approx token count — ~4 chars per token (English)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _pad_to_min_tokens(contents: list, system_prompt: str, min_tokens: int) -> list:
    """32k min ke liye content pad karo. Gemini cache create nahi karega agar kam ho."""
    total = _estimate_tokens(system_prompt) + sum(_estimate_tokens(c) for c in contents)
    if total >= min_tokens:
        return contents
    needed = min_tokens - total
    pad_count = max(1, (needed // _estimate_tokens(_CACHE_FILLER)) + 1)
    padded = (_CACHE_FILLER * pad_count).strip()
    return contents + [padded]


def _is_cache_expired() -> bool:
    """TTL check — 55 min baad proactive re-create. Admin update ke alawa bhi."""
    global _cached_prompt_cache, _cached_prompt_expiry
    if not _cached_prompt_cache or not _cached_prompt_expiry:
        return True
    now = datetime.datetime.now(datetime.timezone.utc)
    return now >= _cached_prompt_expiry


def _get_or_create_cache(api_key: str, model_name: str, system_prompt: str, db=None):
    """System prompt + property data 1 bar cache. Gemini min 32k tokens, TTL 1 hour.
    Agar 32k se kam ho to pad, agar expire ho gaya to re-create."""
    if os.getenv("ENABLE_CONTEXT_CACHE", "true").lower() in ("false", "0", "no"):
        return None
    global _cached_prompt_cache, _cached_prompt_expiry
    if not _is_cache_expired():
        return _cached_prompt_cache

    genai.configure(api_key=api_key)
    cache_model = os.getenv("GEMINI_CACHE_MODEL") or model_name or "gemini-3-flash-preview"

    contents = []
    if db:
        prop_data = _get_property_data_for_cache(db)
        if prop_data:
            contents = [f"Lahore properties (area|type|title|price_lac):\n{prop_data}"]
    if not contents:
        contents = [_CACHE_FILLER]

    # 32k min — kam ho to pad; nahi to Gemini reject kar dega
    contents = _pad_to_min_tokens(contents, system_prompt, MIN_CACHE_TOKENS)

    try:
        cache = genai.caching.CachedContent.create(
            model=cache_model,
            display_name="lpg_property_prompt",
            system_instruction=system_prompt,
            contents=contents,
            ttl=datetime.timedelta(minutes=CACHE_TTL_MINUTES),
        )
        _cached_prompt_cache = cache
        now = datetime.datetime.now(datetime.timezone.utc)
        _cached_prompt_expiry = now + datetime.timedelta(minutes=PROACTIVE_REFRESH_MINUTES)
        return cache
    except Exception as e:
        print(f"[LPG] Cache create failed ({e}), using normal model")
        return None


def _extract_lead_json(text: str) -> dict | None:
    """Extract LEAD_COLLECTED JSON from response."""
    m = re.search(r"LEAD_COLLECTED:\s*(\{.+?\})(?:\s|$)", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    return None


def _strip_internal_metadata_from_text(text: str) -> str:
    """User ko sirf plain text dikhe — FILTER_CRITERIA, LEAD_COLLECTED, koi bhi JSON hatao."""
    if not text:
        return text or ""
    text = re.sub(r"\s*FILTER_CRITERIA\s*:\s*\{[^}]*\}\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*LEAD_COLLECTED\s*:\s*\{[^}]*\}\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


def _extract_filter_criteria(text: str) -> dict:
    """Extract FILTER_CRITERIA JSON from response."""
    m = re.search(r"FILTER_CRITERIA:\s*(\{.+?\})(?:\s|$)", text, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group(1))
            return d if isinstance(d, dict) else {}
        except json.JSONDecodeError:
            pass
    return {}


def _build_filter_from_context(context: list) -> dict:
    """Conversation se area, type, budget extract karo."""
    fc = {}
    full = " ".join([str(c.get("content", "")) for c in context]).lower()
    areas = [("dha", "DHA"), ("bahria", "Bahria"), ("gulberg", "Gulberg"), ("model town", "Model Town"), ("johar", "Johar")]
    for k, v in areas:
        if k in full:
            fc["area"] = v
            break
    if "plot" in full:
        fc["type"] = "plot"
    elif "house" in full or "home" in full:
        fc["type"] = "house"
    elif "flat" in full or "apartment" in full:
        fc["type"] = "flat"
    # Budget: "2 crore" -> 200 lac, "50 lac" -> 50
    m = re.search(r"(\d+)\s*(crore|cr)", full)
    if m:
        fc["budget_max_lac"] = int(m.group(1)) * 100
    else:
        m = re.search(r"(\d+)\s*(lac|lakh|lk)", full)
        if m:
            fc["budget_max_lac"] = int(m.group(1))
    return fc


def _fetch_properties(db, filter_criteria: dict, limit: int = 20):
    """Filter criteria se properties fetch karo. area, type, budget_max_lac."""
    from app.models.property import Property

    q = db.query(Property)
    if filter_criteria:
        area = filter_criteria.get("area")
        if area and str(area).strip():
            q = q.filter(Property.location_name.ilike(f"%{str(area).strip()}%"))
        ptype = filter_criteria.get("type")
        if ptype and str(ptype).strip():
            q = q.filter(Property.type.ilike(f"%{str(ptype).strip()}%"))
        budget_lac = filter_criteria.get("budget_max_lac")
        if budget_lac is not None:
            try:
                max_rupees = float(budget_lac) * 100000
                q = q.filter(Property.price <= max_rupees)
            except (TypeError, ValueError):
                pass
    rows = q.order_by(Property.created_at.desc()).limit(limit).all()
    return [
        {
            "id": p.id,
            "title": p.title or "",
            "location_name": p.location_name or "",
            "price": float(p.price) if p.price else 0,
            "area_size": p.area_size or "",
            "type": p.type or "",
            "cover_photo": p.cover_photo or "",
            "bedrooms": p.bedrooms,
            "baths": p.baths,
        }
        for p in rows
    ]


def _parse_gemini_json_response(text: str):
    """JSON agar hai (```json ya raw {...}) to parse karo. Sirf question text return — bina JSON."""
    if not text or not text.strip():
        return text or "", {}, {}
    stripped = text.strip()

    def _try_parse(json_str: str):
        try:
            data = json.loads(json_str)
            q = data.get("question") or data.get("message") or ""
            lc = data.get("lead_collected") or {}
            fc = data.get("filter_criteria") or {}
            return (str(q).strip(), lc if isinstance(lc, dict) else {}, fc if isinstance(fc, dict) else {})
        except json.JSONDecodeError:
            return None

    # 1. ```json ... ``` ya ``` ... ```
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", stripped, re.DOTALL)
    if m:
        r = _try_parse(m.group(1).strip())
        if r and r[0]:
            return r

    # 2. Raw JSON object { ... }
    if stripped.startswith("{"):
        r = _try_parse(stripped)
        if r and r[0]:
            return r

    return stripped, {}, {}


def _extract_lead_regex(text: str, all_messages: list) -> dict | None:
    """Fallback: regex extract name, phone from conversation."""
    full = " ".join([str(m) for m in all_messages]) + " " + (text or "")
    lead = {}
    # Phone
    phone_m = re.search(r"(\+92\s?\d{2}\s?\d{7}|03\d{2}\s?\d{7}|\d{4}[\s-]?\d{7})", full.replace("-", ""))
    if phone_m:
        lead["phone"] = phone_m.group(1).strip()
    # Name
    for pat in [
        r"(?:mera naam|my name is|I am|naam)\s*[: ]?\s*([A-Za-z\s]+?)(?:\.|,|$)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)",
    ]:
        m = re.search(pat, full, re.I)
        if m:
            lead["name"] = m.group(1).strip()
            break
    return lead if (lead.get("name") and lead.get("phone")) else None


async def get_ai_response(query: str, messages: list, thread_id: str = None, db=None, gemini_settings=None):
    api_key = os.getenv("GEMINI_API_KEY")
    if gemini_settings and gemini_settings.api_key:
        api_key = gemini_settings.api_key
    if not api_key:
        return {
            "question": "API Key missing in .env file",
            "listings": [],
            "message": "",
            "lead_info": None,
            "lead_id": None,
            "lead_collected": {},
            "filter_criteria": {},
        }

    # 1. Load/store messages by thread_id
    stored_messages = []
    if db and thread_id:
        from app.models.chat_message import ChatMessage

        stored = (
            db.query(ChatMessage)
            .filter(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.id)
            .limit(50)
            .all()
        )
        stored_messages = [{"role": m.role, "content": m.content} for m in stored]

    # Merge: prefer stored, fallback to incoming messages
    if stored_messages:
        context = stored_messages
    else:
        context = [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages]

    # Sanitize: assistant content agar JSON hai to sirf question text use karo (Gemini ko clean history mile)
    def _clean_content(role: str, content: str) -> str:
        if role not in ("model", "assistant") or not content:
            return content or ""
        q, _, _ = _parse_gemini_json_response(content)
        return q if q else content

    for c in context:
        c["content"] = _clean_content(c.get("role", ""), c.get("content", ""))

    # Add new user message
    if query and query.strip():
        context.append({"role": "user", "content": query.strip()})

    # 2. Build Gemini history (last N only — caching for speed)
    history = context[-(MAX_CONTEXT_MESSAGES + 1) :] if len(context) > MAX_CONTEXT_MESSAGES else context

    system_prompt = LEAD_COLLECT_PROMPT
    if gemini_settings:
        if gemini_settings.system_instructions:
            system_prompt = gemini_settings.system_instructions
        if gemini_settings.conversation_instructions:
            system_prompt += "\n\n" + gemini_settings.conversation_instructions

    genai.configure(api_key=api_key)
    from app.core.config import get_gemini_model
    model_name = (gemini_settings.model if gemini_settings else None) or get_gemini_model()
    if not model_name or model_name == "gemini-1.5-flash":
        model_name = get_gemini_model()

    def _is_cache_expired_error(exc: Exception) -> bool:
        s = str(exc).lower()
        return any(k in s for k in ("expired", "not found", "invalid", "404", "cached"))

    raw = None
    for attempt in range(2):
        try:
            cache = _get_or_create_cache(api_key, model_name, system_prompt, db=db)
            if cache:
                model = genai.GenerativeModel.from_cached_content(cache)
            else:
                model = genai.GenerativeModel(model_name, system_instruction=system_prompt)

            chat_history = []
            for i in range(0, len(history) - 1, 2):
                if i + 1 < len(history):
                    u = history[i]
                    m = history[i + 1]
                    if u.get("role") == "user" and m.get("role") in ("model", "assistant"):
                        chat_history.append({"role": "user", "parts": [u.get("content", "")]})
                        chat_history.append({"role": "model", "parts": [m.get("content", "")]})

            if chat_history:
                chat = model.start_chat(history=chat_history)
                last_user = history[-1].get("content", "") if history else query
                response = chat.send_message(last_user)
            else:
                user_msg = query or (history[-1].get("content", "") if history else "")
                if cache:
                    response = model.generate_content(user_msg)
                else:
                    response = model.generate_content(f"{system_prompt}\n\nUser: {user_msg}")

            raw = response.text if response and response.text else "AI response empty."
            break
        except Exception as e:
            if attempt == 0 and _is_cache_expired_error(e):
                invalidate_gemini_cache()
                continue
            raise

    if raw is None:
        raw = "AI response empty."

    try:
        # 2.5 Parse json block agar hai — clean question + lead_collected + filter_criteria
        question, parsed_lead, filter_criteria = _parse_gemini_json_response(raw)
        if not question:
            question = raw
        # Chat reply se FILTER_CRITERIA: {...} hatao — user ko sirf question dikhe
        question = _strip_internal_metadata_from_text(question)

        # 2.6 Filter criteria — JSON, FILTER_CRITERIA:, ya context se
        fc2 = _extract_filter_criteria(raw)
        if fc2:
            filter_criteria = {**filter_criteria, **{k: v for k, v in fc2.items() if v is not None}}
        if not filter_criteria:
            filter_criteria = _build_filter_from_context(context)

        # 2.7 Properties fetch — filter_criteria se (empty = sab dikhao)
        listings = []
        if db:
            listings = _fetch_properties(db, filter_criteria)

        # 3. Extract lead (prefer parsed_lead, then JSON, else regex)
        lead_info = None
        if parsed_lead and parsed_lead.get("name") and parsed_lead.get("phone"):
            lead_info = parsed_lead
        else:
            lead_info = _extract_lead_json(raw) or _extract_lead_regex(raw, context)
        lead_id = None

        if db and lead_info and lead_info.get("name") and lead_info.get("phone"):
            import uuid
            from app.models.lead import Lead

            existing = db.query(Lead).filter(Lead.thread_id == thread_id).first() if thread_id else None
            if existing:
                existing.name = lead_info.get("name") or existing.name
                existing.phone = lead_info.get("phone") or existing.phone
                existing.budget = lead_info.get("budget") or existing.budget
                existing.property_interest = lead_info.get("interest") or lead_info.get("property_interest") or existing.property_interest
                existing.ai_summary = (question[:300] or existing.ai_summary) if question else existing.ai_summary
                existing.context = str(context)[:500] if context else existing.context
                db.commit()
                db.refresh(existing)
                lead_id = existing.id
            else:
                new_id = "L" + str(uuid.uuid4())[:8].upper()
                lead = Lead(
                    id=new_id,
                    name=lead_info.get("name"),
                    phone=lead_info.get("phone"),
                    user_name=lead_info.get("name") or "Visitor",
                    budget=lead_info.get("budget"),
                    property_interest=lead_info.get("interest") or lead_info.get("property_interest"),
                    context=str(context)[:500] if context else None,
                    ai_summary=question[:300] if question else None,
                    source="AI Search",
                    thread_id=thread_id,
                )
                db.add(lead)
                db.commit()
                db.refresh(lead)
                lead_id = lead.id

            if lead_info:
                lead_info["lead_id"] = lead_id

        # 4. Save messages for thread (only if thread_id)
        if db and thread_id and raw:
            from app.models.chat_message import ChatMessage

            if query and query.strip():
                db.add(ChatMessage(thread_id=thread_id, role="user", content=query.strip()))
            db.add(ChatMessage(thread_id=thread_id, role="model", content=question or raw))
            db.commit()

        return {
            "question": question,
            "listings": listings,
            "message": "",
            "lead_info": lead_info,
            "lead_id": lead_id,
            "lead_collected": lead_info or parsed_lead or {},
            "filter_criteria": filter_criteria,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"question": f"Error: {str(e)}", "listings": [], "message": "", "lead_info": None, "lead_id": None, "lead_collected": {}, "filter_criteria": {}}
