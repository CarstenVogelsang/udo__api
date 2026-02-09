"""
Business logic for ETL (Extract-Transform-Load) operations.

Provides:
- CRUD operations for Sources, TableMappings, FieldMappings
- Transformation registry for field transformations
- Import logic with FK lookups
"""
import re
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.etl import (
    EtlSource,
    EtlTableMapping,
    EtlFieldMapping,
    EtlImportLog,
)
from app.schemas.etl import (
    EtlSourceCreate,
    EtlSourceUpdate,
    EtlTableMappingCreate,
    EtlTableMappingUpdate,
    EtlFieldMappingCreate,
    EtlFieldMappingUpdate,
)


# ============ Transformation Registry ============

def _trim(value: Any) -> Any:
    """Strip whitespace from strings."""
    if isinstance(value, str):
        return value.strip()
    return value


def _upper(value: Any) -> Any:
    """Convert to uppercase."""
    if isinstance(value, str):
        return value.upper()
    return value


def _lower(value: Any) -> Any:
    """Convert to lowercase."""
    if isinstance(value, str):
        return value.lower()
    return value


def _to_int(value: Any) -> int | None:
    """Convert to integer."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _to_float(value: Any) -> float | None:
    """Convert to float."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_str(value: Any) -> str | None:
    """Convert to string."""
    if value is None:
        return None
    return str(value)


# ============ Excel Import Transformations ============

def _split_street_name(value: Any) -> Any:
    """Extract street name: 'Glender Weg 6' -> 'Glender Weg'."""
    if not isinstance(value, str) or not value.strip():
        return value
    match = re.match(r'^(.+?)\s+(\d+\s*\w?)$', value.strip())
    return match.group(1).strip() if match else value.strip()


def _split_street_hausnr(value: Any) -> Any:
    """Extract house number: 'Glender Weg 6' -> '6'."""
    if not isinstance(value, str) or not value.strip():
        return None
    match = re.match(r'^(.+?)\s+(\d+\s*\w?)$', value.strip())
    return match.group(2).strip() if match else None


def _normalize_phone(value: Any) -> Any:
    """Normalize phone: '+49 (0)9574 65464-0' -> '095746546400'."""
    if not isinstance(value, str) or not value.strip():
        return value
    phone = value.strip()
    phone = re.sub(r'^\+49\s*', '0', phone)
    phone = re.sub(r'^0049\s*', '0', phone)
    phone = re.sub(r'[^\d]', '', phone)
    return phone if phone else value


def _normalize_plz(value: Any) -> Any:
    """Pad German PLZ to 5 digits: 1234 -> '01234'."""
    if value is None:
        return None
    plz_str = str(value).strip()
    plz_str = re.sub(r'[^\d]', '', plz_str)
    if not plz_str:
        return None
    return plz_str.zfill(5)


def _normalize_url(value: Any) -> Any:
    """Normalize URL: 'https://www.hoellein.com/' -> 'hoellein.com'."""
    if not isinstance(value, str) or not value.strip():
        return value
    url = value.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url


def _normalize_email(value: Any) -> Any:
    """Normalize email: trim + lowercase."""
    if not isinstance(value, str) or not value.strip():
        return value
    return value.strip().lower()


def _extract_anrede(value: Any) -> Any:
    """Extract Anrede: 'Sehr geehrter Herr' -> 'Herr'."""
    if not isinstance(value, str) or not value.strip():
        return value
    val = value.strip()
    if 'Herr' in val:
        return 'Herr'
    if 'Frau' in val:
        return 'Frau'
    return val


# Registry of available transformations
TRANSFORMS: dict[str, Callable[[Any], Any]] = {
    "trim": _trim,
    "upper": _upper,
    "lower": _lower,
    "to_int": _to_int,
    "to_float": _to_float,
    "to_str": _to_str,
    "split_street_name": _split_street_name,
    "split_street_hausnr": _split_street_hausnr,
    "normalize_phone": _normalize_phone,
    "normalize_plz": _normalize_plz,
    "normalize_url": _normalize_url,
    "normalize_email": _normalize_email,
    "extract_anrede": _extract_anrede,
}


class EtlService:
    """Service class for ETL operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._fk_cache: dict[str, dict[Any, str]] = {}

    # ============ EtlSource CRUD ============

    async def get_sources(self, skip: int = 0, limit: int = 100) -> dict:
        """Get all ETL sources."""
        count_query = select(func.count(EtlSource.id))
        total = (await self.db.execute(count_query)).scalar()

        query = (
            select(EtlSource)
            .order_by(EtlSource.name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_source_by_id(self, source_id: str) -> EtlSource | None:
        """Get a single source by ID."""
        query = (
            select(EtlSource)
            .options(selectinload(EtlSource.table_mappings))
            .where(EtlSource.id == source_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_source_by_name(self, name: str) -> EtlSource | None:
        """Get a single source by name."""
        query = (
            select(EtlSource)
            .options(selectinload(EtlSource.table_mappings))
            .where(EtlSource.name == name)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_source(self, data: EtlSourceCreate) -> EtlSource:
        """Create a new ETL source."""
        source = EtlSource(**data.model_dump())
        self.db.add(source)
        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def update_source(self, source_id: str, data: EtlSourceUpdate) -> EtlSource | None:
        """Update an existing ETL source."""
        source = await self.get_source_by_id(source_id)
        if not source:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(source, key, value)

        await self.db.flush()
        await self.db.refresh(source)
        return source

    async def delete_source(self, source_id: str) -> bool:
        """Delete an ETL source."""
        source = await self.get_source_by_id(source_id)
        if not source:
            return False

        await self.db.delete(source)
        return True

    # ============ EtlTableMapping CRUD ============

    async def get_table_mappings(
        self,
        source_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get table mappings, optionally filtered by source."""
        base_query = select(EtlTableMapping).options(
            joinedload(EtlTableMapping.source)
        )

        if source_id:
            base_query = base_query.where(EtlTableMapping.source_id == source_id)

        count_query = select(func.count(EtlTableMapping.id))
        if source_id:
            count_query = count_query.where(EtlTableMapping.source_id == source_id)
        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(EtlTableMapping.source_table).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def get_table_mapping_by_id(self, mapping_id: str) -> EtlTableMapping | None:
        """Get a single table mapping by ID with field mappings."""
        query = (
            select(EtlTableMapping)
            .options(
                joinedload(EtlTableMapping.source),
                selectinload(EtlTableMapping.field_mappings),
            )
            .where(EtlTableMapping.id == mapping_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_table_mapping_by_tables(
        self,
        source_id: str,
        source_table: str,
        target_table: str
    ) -> EtlTableMapping | None:
        """Get a table mapping by source and target table names."""
        query = (
            select(EtlTableMapping)
            .options(
                joinedload(EtlTableMapping.source),
                selectinload(EtlTableMapping.field_mappings),
            )
            .where(
                EtlTableMapping.source_id == source_id,
                EtlTableMapping.source_table == source_table,
                EtlTableMapping.target_table == target_table,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_table_mapping(self, data: EtlTableMappingCreate) -> EtlTableMapping:
        """Create a new table mapping."""
        mapping = EtlTableMapping(**data.model_dump())
        self.db.add(mapping)
        await self.db.flush()
        await self.db.refresh(mapping)
        return mapping

    async def update_table_mapping(
        self,
        mapping_id: str,
        data: EtlTableMappingUpdate
    ) -> EtlTableMapping | None:
        """Update an existing table mapping."""
        mapping = await self.get_table_mapping_by_id(mapping_id)
        if not mapping:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mapping, key, value)

        await self.db.flush()
        await self.db.refresh(mapping)
        return mapping

    async def delete_table_mapping(self, mapping_id: str) -> bool:
        """Delete a table mapping."""
        mapping = await self.get_table_mapping_by_id(mapping_id)
        if not mapping:
            return False

        await self.db.delete(mapping)
        return True

    # ============ EtlFieldMapping CRUD ============

    async def get_field_mappings(
        self,
        table_mapping_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get field mappings, optionally filtered by table mapping."""
        base_query = select(EtlFieldMapping)

        if table_mapping_id:
            base_query = base_query.where(EtlFieldMapping.table_mapping_id == table_mapping_id)

        count_query = select(func.count(EtlFieldMapping.id))
        if table_mapping_id:
            count_query = count_query.where(EtlFieldMapping.table_mapping_id == table_mapping_id)
        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(EtlFieldMapping.source_field).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_field_mapping_by_id(self, mapping_id: str) -> EtlFieldMapping | None:
        """Get a single field mapping by ID."""
        query = (
            select(EtlFieldMapping)
            .options(joinedload(EtlFieldMapping.table_mapping))
            .where(EtlFieldMapping.id == mapping_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_field_mapping(self, data: EtlFieldMappingCreate) -> EtlFieldMapping:
        """Create a new field mapping."""
        mapping = EtlFieldMapping(**data.model_dump())
        self.db.add(mapping)
        await self.db.flush()
        await self.db.refresh(mapping)
        return mapping

    async def update_field_mapping(
        self,
        mapping_id: str,
        data: EtlFieldMappingUpdate
    ) -> EtlFieldMapping | None:
        """Update an existing field mapping."""
        mapping = await self.get_field_mapping_by_id(mapping_id)
        if not mapping:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(mapping, key, value)

        await self.db.flush()
        await self.db.refresh(mapping)
        return mapping

    async def delete_field_mapping(self, mapping_id: str) -> bool:
        """Delete a field mapping."""
        mapping = await self.get_field_mapping_by_id(mapping_id)
        if not mapping:
            return False

        await self.db.delete(mapping)
        return True

    # ============ EtlImportLog ============

    async def get_import_logs(
        self,
        table_mapping_id: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> dict:
        """Get import logs, optionally filtered by table mapping."""
        base_query = select(EtlImportLog).options(
            joinedload(EtlImportLog.table_mapping)
        )

        if table_mapping_id:
            base_query = base_query.where(EtlImportLog.table_mapping_id == table_mapping_id)

        count_query = select(func.count(EtlImportLog.id))
        if table_mapping_id:
            count_query = count_query.where(EtlImportLog.table_mapping_id == table_mapping_id)
        total = (await self.db.execute(count_query)).scalar()

        query = base_query.order_by(EtlImportLog.started_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        items = result.scalars().unique().all()

        return {"items": items, "total": total}

    async def create_import_log(self, table_mapping_id: str) -> EtlImportLog:
        """Create a new import log entry."""
        log = EtlImportLog(
            table_mapping_id=table_mapping_id,
            status="running",
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def update_import_log(
        self,
        log: EtlImportLog,
        status: str,
        records_read: int = 0,
        records_created: int = 0,
        records_updated: int = 0,
        records_failed: int = 0,
        error_message: str | None = None
    ) -> EtlImportLog:
        """Update an import log entry."""
        log.status = status
        log.records_read = records_read
        log.records_created = records_created
        log.records_updated = records_updated
        log.records_failed = records_failed
        log.error_message = error_message
        log.finished_at = datetime.utcnow()
        await self.db.flush()
        return log

    # ============ Transformation Helpers ============

    async def build_fk_lookup_cache(self, table: str, lookup_field: str) -> dict[Any, str]:
        """
        Build a lookup cache for foreign key resolution.

        Args:
            table: Target table name (e.g., "geo_ort")
            lookup_field: Field to lookup by (e.g., "legacy_id")

        Returns:
            Dict mapping lookup_field values to id values
        """
        cache_key = f"{table}.{lookup_field}"
        if cache_key in self._fk_cache:
            return self._fk_cache[cache_key]

        # Build the lookup query dynamically
        query = text(f"SELECT {lookup_field}, id FROM {table} WHERE {lookup_field} IS NOT NULL")
        result = await self.db.execute(query)
        rows = result.fetchall()

        cache = {row[0]: row[1] for row in rows}
        self._fk_cache[cache_key] = cache
        return cache

    def apply_transform(
        self,
        value: Any,
        transform: str | None,
        fk_caches: dict[str, dict[Any, str]] | None = None
    ) -> Any:
        """
        Apply a transformation to a value.

        Args:
            value: The value to transform
            transform: Transformation name or "fk_lookup:table.field"
            fk_caches: Pre-built FK lookup caches

        Returns:
            Transformed value
        """
        if transform is None:
            return value

        # Handle FK lookup transformation
        if transform.startswith("fk_lookup:"):
            if fk_caches is None:
                return None

            # Parse "fk_lookup:geo_ort.legacy_id"
            lookup_spec = transform[10:]  # Remove "fk_lookup:"
            if "." in lookup_spec:
                table, field = lookup_spec.split(".", 1)
                cache_key = f"{table}.{field}"
                if cache_key in fk_caches:
                    return fk_caches[cache_key].get(value)
            return None

        # Handle standard transformations
        if transform in TRANSFORMS:
            return TRANSFORMS[transform](value)

        # Unknown transformation - return value unchanged
        return value

    def get_available_transforms(self) -> list[str]:
        """Get list of available transformation names."""
        return list(TRANSFORMS.keys()) + ["fk_lookup:<table>.<field>"]
