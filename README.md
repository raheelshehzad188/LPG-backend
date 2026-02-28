# Lahore Property Guide — Backend API

FastAPI backend for LPG (Lahore Property Guide) — Admin Panel, Partner Panel, AI Chat.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in DB + Gemini keys.

```bash
python scripts/init_db.py
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Docs

Postman collections:
- **All APIs:** `docs/LPG_Complete_API.postman_collection.json`
- **Partner Panel:** `docs/LPG_Partner_Panel_API.postman_collection.json`

Base URL: `http://127.0.0.1:8000`
