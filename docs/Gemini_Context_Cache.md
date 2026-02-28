# Gemini Context Cache — Kaam Kaise Hota Hai

## Overview

LPG AI har user message ke liye Gemini API call karta hai. Har call mein **system prompt** (instructions) + **property data** (Lahore listings) bhejna padta hai — ye same content har request par repeat hota hai. Isko optimize karne ke liye **Gemini Context Caching** use karte hain: ye content **ek bar** cache ho jata hai, phir next 1 hour tak **har request** is cached context ke saath chalati hai. Isse:
- Response time fast rehta hai
- API cost kam hoti hai (cached content free/counted differently)
- System prompt + property data har bar nahi bhejna padta

---

## Flow — Step by Step

```
User Message → AI Engine → Cache Check
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Cache Maujood?       Cache Expired / Nahi?
              (55 min andar)            │
                    │                   │
                    │                   ▼
                    │         [Create New Cache]
                    │         - System prompt
                    │         - Property data (500 listings)
                    │         - Pad to 32k tokens
                    │         - Gemini API: CachedContent.create
                    │                   │
                    └──────────┬────────┘
                               │
                               ▼
                    Model = from_cached_content(cache)
                               │
                               ▼
                    generate_content(user_message)
                               │
                               ▼
                    Response → Parse → Lead / Filter / Listings
```

---

## Cache Create Kab Hota Hai?

| Condition | Action |
|-----------|--------|
| Pehli AI request | Naya cache create |
| Cache 55+ min purana | Purana invalidate, naya create |
| Admin ne instructions update kiye | Purana delete, next request pe naya create |
| Cache use karte waqt API "expired" error | Invalidate + retry (1 bar) |
| `ENABLE_CONTEXT_CACHE=false` | Cache bilkul nahi, har bar normal model |

---

## 32k Token Minimum — Kya Matlab?

Gemini API ko cache create karne ke liye **minimum ~32,768 tokens** chahiye. Agar system prompt + property data mila kar isse kam hon, cache create **fail** ho jata hai.

**Solution:** Hum `_pad_to_min_tokens()` use karte hain:
- Pehle total tokens estimate karte hain (chars / 4)
- Agar < 32k ho, to `_CACHE_FILLER` (area list, types, price examples) repeat karke pad karte hain
- Phir cache create karte hain

**Fallback:** Agar cache create phir bhi fail (e.g. model support nahi), to normal `system_instruction` ke saath model use hoti hai — AI kaam karti hai, sirf cache benefit nahi milta.

---

## TTL (Time to Live) — 1 Hour

- **Gemini default:** Cache 1 hour (60 min) baad expire ho jata hai
- **Proactive refresh:** Hum 55 min pe **khud** cache expire maan kar naya create kar dete hain — taake user request ke dauran "expired" error na aaye
- `_cached_prompt_expiry` in-memory store karta hai kab refresh karna hai

---

## Admin Update → Cache Invalidate

Jab admin **PUT /api/gemini** se system instructions / conversation instructions update karta hai:
1. `invalidate_gemini_cache()` call hota hai
2. Purana cache Gemini API par se `delete()` ho jata hai
3. In-memory `_cached_prompt_cache = None`
4. **Next** AI request pe naya cache naye instructions ke saath create hoga

Same **POST /api/gemini/reset** par bhi — default instructions ke liye cache refresh.

---

## Manual Cache Refresh

Admin chahe to force refresh kar sakta hai:
```
POST /api/gemini/refresh-cache
Authorization: Bearer <admin_token>
```
Response: `{"success": true, "message": "Cache invalidated. Next AI request will create fresh cache."}`

---

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CONTEXT_CACHE` | `true` | `false` = cache band |
| `GEMINI_CACHE_MODEL` | — | Cache ke liye model (1.5 recommended) |
| `GEMINI_CACHE_TTL_MINUTES` | `60` | Cache 60 min tak valid |
| `GEMINI_CACHE_REFRESH_MINUTES` | `55` | 55 min pe proactive re-create |
| `GEMINI_MIN_CACHE_TOKENS` | `32768` | Min tokens — kam ho to pad |

---

## Code Reference

- `app/core/ai_engine.py`: `_get_or_create_cache()`, `invalidate_gemini_cache()`, `_pad_to_min_tokens()`
- `app/api/gemini.py`: `save_gemini_settings`, `reset_gemini_instructions`, `refresh_gemini_cache`
