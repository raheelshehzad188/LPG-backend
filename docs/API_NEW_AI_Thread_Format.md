# api_new_ai — Thread-based AI Chat API

## Endpoint
```
POST /api_new_ai
```
Base URL: `http://127.0.0.1:8000` (ya production URL)

---

## Request Format

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | User ka current message |
| `threadId` | string | **Yes** | Unique chat session ID (har user/chat ke liye alag) |
| `messages` | array | No | Backend thread se load karta hai — empty bhej sakte ho agar threadId diya hai |

---

## cURL Examples

### 1. New User — First Message (empty messages)
```bash
curl -X POST 'http://127.0.0.1:8000/api_new_ai' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -d '{
    "query": "DHA Phase 9 mein plot chahta hoon",
    "threadId": "550e8400-e29b-41d4-a716-446655440000",
    "messages": []
  }'
```

### 2. Same User — Continue Chat (threadId same rakho)
```bash
curl -X POST 'http://127.0.0.1:8000/api_new_ai' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "2 crore budget hai",
    "threadId": "550e8400-e29b-41d4-a716-446655440000",
    "messages": []
  }'
```

### 3. Different User — New Thread (naya threadId)
```bash
curl -X POST 'http://127.0.0.1:8000/api_new_ai' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "Bahria Town flat",
    "threadId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "messages": []
  }'
```

---

## Response Format

```json
{
  "question": "AI ka reply text...",
  "listings": [],
  "message": "",
  "lead_info": {
    "name": "Ahmed Khan",
    "phone": "03001234567",
    "budget": "2 crore",
    "interest": "DHA Phase 9 plot"
  },
  "lead_id": "L1A2B3C4",
  "lead_collected": { ... },
  "filter_criteria": {}
}
```

| Field | Description |
|-------|-------------|
| `question` | AI ka reply (frontend mein display) |
| `listings` | Property list (abhi empty) |
| `lead_id` | Jab name+phone mil jaye — backend lead create karta hai, ID yahan aati hai |
| `lead_collected` | Extracted lead data (name, phone, budget, interest) |

---

## Frontend Changes — Checklist

### 1. threadId Generate + Store
- Har naye chat ke liye **unique threadId** banao
- `crypto.randomUUID()` ya `Date.now() + random string`
- **localStorage** mein `lpg_ai_thread_id` key se save karo
- "New Chat" / "Fresh Search" pe naya threadId generate karo

### 2. Request Body
```javascript
{
  query: userMessage,           // string
  threadId: getOrCreateThreadId(),  // zaroori
  messages: []                  // backend load karega — empty bhejo
}
```

### 3. Pehle se `messages` bhej rahe ho?
- Agar purane code mein `messages` array bhej rahe the, **remove** karo
- Backend ab `threadId` se DB se history load karta hai
- `messages: []` bhejna kaafi hai

### 4. "New Chat" / "Fresh Session"
- `localStorage.removeItem('lpg_ai_thread_id')`
- Naya `threadId` generate karo
- Page refresh ya new chat button pe ye karo

---

## Optional: `thread_id` (snake_case)
Backend dono accept karta hai:
- `threadId` (camelCase)
- `thread_id` (snake_case)

---

## Example: Frontend Fetch

```javascript
const threadId = localStorage.getItem('lpg_ai_thread_id') || crypto.randomUUID();
if (!localStorage.getItem('lpg_ai_thread_id')) {
  localStorage.setItem('lpg_ai_thread_id', threadId);
}

const res = await fetch('/api_new_ai', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    query: 'DHA plot',
    threadId,
    messages: []
  })
});

const data = await res.json();
console.log(data.question);  // AI reply
console.log(data.lead_id);  // Lead ID when collected
```
