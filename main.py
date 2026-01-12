"""
Root entry point for Nixpacks deployment.

This file re-exports the FastAPI app from app.main for compatibility
with the Nixpacks deployment configuration.
"""
from app.main import app

# Re-export for: fastapi run main.py
__all__ = ["app"]
