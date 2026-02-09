"""
Business logic for Smart Filter management.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.smart_filter import SmartFilter
from app.schemas.smart_filter import SmartFilterCreate, SmartFilterUpdate


class SmartFilterService:
    """Service class for Smart Filter CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_filters(
        self,
        entity_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """Get all smart filters, optionally filtered by entity type."""
        count_query = select(func.count(SmartFilter.id))
        base_query = select(SmartFilter)

        if entity_type:
            count_query = count_query.where(SmartFilter.entity_type == entity_type)
            base_query = base_query.where(SmartFilter.entity_type == entity_type)

        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(SmartFilter.name).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_filter_by_id(self, filter_id: str) -> SmartFilter | None:
        """Get a single smart filter by ID."""
        query = select(SmartFilter).where(SmartFilter.id == filter_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_filter(self, data: SmartFilterCreate) -> SmartFilter:
        """Create a new smart filter."""
        smart_filter = SmartFilter(
            name=data.name,
            beschreibung=data.beschreibung,
            entity_type=data.entity_type,
            dsl_expression=data.dsl_expression,
        )
        self.db.add(smart_filter)
        await self.db.commit()
        await self.db.refresh(smart_filter)
        return smart_filter

    async def update_filter(
        self,
        filter_id: str,
        data: SmartFilterUpdate,
    ) -> SmartFilter | None:
        """Update an existing smart filter."""
        smart_filter = await self.get_filter_by_id(filter_id)
        if not smart_filter:
            return None

        update_data = {k: v for k, v in data.model_dump().items() if v is not None}
        for key, value in update_data.items():
            setattr(smart_filter, key, value)

        await self.db.commit()
        await self.db.refresh(smart_filter)
        return smart_filter

    async def delete_filter(self, filter_id: str) -> bool:
        """Delete a smart filter."""
        smart_filter = await self.get_filter_by_id(filter_id)
        if not smart_filter:
            return False

        await self.db.delete(smart_filter)
        await self.db.commit()
        return True
