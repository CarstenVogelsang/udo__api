"""
Business logic for API Partner management.
"""
import secrets
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.partner import ApiPartner
from app.auth import hash_api_key
from app.schemas.partner import ApiPartnerCreate, ApiPartnerUpdate


def generate_api_key() -> str:
    """Generates a secure random API key."""
    return secrets.token_urlsafe(32)


class PartnerService:
    """Service class for Partner operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_partners(self, skip: int = 0, limit: int = 100) -> dict:
        """Get all partners."""
        # Count
        count_query = select(func.count(ApiPartner.id))
        total = (await self.db.execute(count_query)).scalar()

        # Data
        query = (
            select(ApiPartner)
            .order_by(ApiPartner.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_partner_by_id(self, partner_id: str) -> ApiPartner | None:
        """Get a partner by ID."""
        query = select(ApiPartner).where(ApiPartner.id == partner_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_partner(self, data: ApiPartnerCreate) -> tuple[ApiPartner, str]:
        """
        Create a new partner with generated API key.

        Returns:
            Tuple of (partner, plain_api_key)
            The plain API key is only returned once!
        """
        # Generate API key
        plain_api_key = generate_api_key()
        key_hash = hash_api_key(plain_api_key)

        # Create partner
        partner = ApiPartner(
            api_key_hash=key_hash,
            name=data.name,
            email=data.email,
            role=data.role,
            kosten_geoapi_pro_einwohner=data.kosten_geoapi_pro_einwohner,
        )

        self.db.add(partner)
        await self.db.flush()
        await self.db.refresh(partner)

        return partner, plain_api_key

    async def update_partner(
        self,
        partner_id: str,
        data: ApiPartnerUpdate
    ) -> ApiPartner | None:
        """Update a partner (partial update)."""
        partner = await self.get_partner_by_id(partner_id)
        if not partner:
            return None

        # Only update provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(partner, field, value)

        await self.db.flush()
        await self.db.refresh(partner)
        return partner

    async def delete_partner(self, partner_id: str) -> bool:
        """Delete a partner."""
        partner = await self.get_partner_by_id(partner_id)
        if not partner:
            return False

        await self.db.delete(partner)
        await self.db.flush()
        return True

    async def regenerate_api_key(self, partner_id: str) -> tuple[ApiPartner, str] | None:
        """
        Regenerate API key for a partner.

        Returns:
            Tuple of (partner, new_plain_api_key) or None if partner not found
        """
        partner = await self.get_partner_by_id(partner_id)
        if not partner:
            return None

        # Generate new API key
        plain_api_key = generate_api_key()
        key_hash = hash_api_key(plain_api_key)

        partner.api_key_hash = key_hash
        await self.db.flush()
        await self.db.refresh(partner)

        return partner, plain_api_key
