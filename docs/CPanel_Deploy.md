# cPanel Deployment (Namecheap)

## Setup Python App — Field Values

| Field | Value |
|-------|-------|
| **Python version** | 3.10 or 3.11 |
| **Application root** | `/home/cPanel_user/yourdomain.com` (your project folder path) |
| **Application URL** | `/` |
| **Application startup file** | `passenger_wsgi.py` |
| **Application entry point** | `application` |

## Steps

1. Upload project files to Application root folder.
2. In Setup Python App, add `requirements.txt` under Configuration files, then click **Run Pip Install**.
3. Set **Environment variables** (DB_USER, DB_PASS, DB_HOST, DB_NAME, SECRET_KEY, GEMINI_API_KEY, etc.).
4. Create MySQL database in cPanel → MySQL Databases.
5. Run DB init (Terminal): `python scripts/init_db.py`
6. Restart the app.

## Important

- **Shared hosting**: ASGI/FastAPI is **not supported** on Namecheap Shared. You need **VPS or Dedicated Server**.
- `passenger_wsgi.py` uses `a2wsgi` to wrap FastAPI (ASGI) for Passenger (WSGI).
