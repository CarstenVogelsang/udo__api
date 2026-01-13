#!/usr/bin/env python3
"""
Test script for JWT authentication.

Usage:
    uv run python scripts/test_jwt_auth.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import select

from app.database import init_db, async_session_maker
from app.models.partner import ApiPartner

BASE_URL = "http://localhost:8001/api/v1"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"


async def setup_test_partner():
    """Ensure test partner has an email and password set."""
    await init_db()

    from app.services.jwt_service import hash_password

    async with async_session_maker() as db:
        # Get first superadmin
        result = await db.execute(
            select(ApiPartner).where(ApiPartner.role == "superadmin").limit(1)
        )
        partner = result.scalar_one_or_none()

        if not partner:
            print("❌ Kein Superadmin gefunden!")
            return None

        # Set email and password directly for testing
        partner.email = TEST_EMAIL
        partner.password_hash = hash_password(TEST_PASSWORD)
        await db.commit()
        print(f"✓ Partner '{partner.name}' mit Email '{TEST_EMAIL}' und Passwort konfiguriert")

        return partner.id


async def main():
    print("=" * 60)
    print("UDO API - JWT Auth Test")
    print("=" * 60)

    # 1. Setup test partner
    print("\n[1/4] Setup Testpartner...")
    partner_id = await setup_test_partner()

    if not partner_id:
        return

    async with httpx.AsyncClient() as client:
        # 2. Test login
        print("\n[2/4] Login mit Email und Passwort...")
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        )

        if resp.status_code != 200:
            print(f"❌ Login fehlgeschlagen: {resp.status_code} - {resp.text}")
            return

        tokens = resp.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print(f"✓ Login erfolgreich!")
        print(f"  Access Token: {access_token[:50]}...")
        print(f"  Refresh Token: {refresh_token[:50]}...")
        print(f"  Expires in: {tokens['expires_in']}s")

        # 3. Test /me endpoint
        print("\n[3/4] Abrufen von /auth/me via JWT...")
        resp = await client.get(
            f"{BASE_URL}/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if resp.status_code != 200:
            print(f"❌ /me fehlgeschlagen: {resp.status_code} - {resp.text}")
            return

        user = resp.json()
        print(f"✓ User Info abgerufen:")
        print(f"  ID: {user['id'][:8]}...")
        print(f"  Name: {user['name']}")
        print(f"  Email: {user['email']}")
        print(f"  Role: {user['role']}")

        # 4. Test token refresh
        print("\n[4/4] Token Refresh...")
        resp = await client.post(
            f"{BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        if resp.status_code != 200:
            print(f"❌ Refresh fehlgeschlagen: {resp.status_code} - {resp.text}")
            return

        new_token = resp.json()
        print(f"✓ Token erneuert!")
        print(f"  New Access Token: {new_token['access_token'][:50]}...")

    print("\n" + "=" * 60)
    print("✅ Alle Tests erfolgreich!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
