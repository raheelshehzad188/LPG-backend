"""WSGI entry point for cPanel / Passenger (ASGI-to-WSGI bridge)."""
from a2wsgi import ASGIMiddleware
from main import app

application = ASGIMiddleware(app)
