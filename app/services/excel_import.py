"""
Excel Import Service for Unternehmen + Kontakt data.

Processes Excel files using ETL configuration (EtlSource with connection_type="excel").
Features:
- Multi-stage deduplication with cascading priority
- Field-level update rules (always, if_empty, never)
- Multiple external IDs per entity
- GeoOrt resolution by PLZ
- Batch commits for large imports
"""
import logging
import uuid
from datetime import datetime
from io import BytesIO
from typing import Any

from openpyxl import load_workbook
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.com import ComUnternehmen, ComKontakt, ComExternalId
from app.models.etl import EtlSource, EtlTableMapping, EtlFieldMapping, EtlImportLog
from app.models.geo import Base, generate_uuid
from app.services.etl import TRANSFORMS

logger = logging.getLogger(__name__)

BATCH_SIZE = 500


class ExcelImportService:
    """Processes Excel file imports for Unternehmen + Kontakt data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        # Dedup caches (loaded once, O(1) lookup per row)
        self._plz_cache: dict[str, str] = {}         # normalized PLZ -> geo_ort.id
        self._email_cache: dict[str, str] = {}        # normalized email -> unternehmen.id
        self._url_cache: dict[str, str] = {}          # normalized url -> unternehmen.id
        self._phone_cache: dict[str, str] = {}        # normalized phone -> unternehmen.id
        self._address_cache: dict[str, str] = {}      # "plz|strasse" -> unternehmen.id
        self._name_cache: dict[str, str] = {}         # normalized firmierung -> unternehmen.id
        self._extid_cache: dict[str, str] = {}        # "source:type:value" -> entity_id
        self._entity_extid_set: set[str] = set()     # "entity_type:entity_id:source:type"

    async def run_import(
        self,
        source_name: str,
        file_content: bytes,
        dry_run: bool = False,
    ) -> dict:
        """
        Main entry point: Parse Excel, apply mappings, dedup, upsert.

        Returns dict with import statistics.
        """
        batch_id = str(uuid.uuid4())

        # 1. Load ETL configuration
        source, u_mapping, k_mapping, u_fields, k_fields, extid_fields = (
            await self._load_config(source_name)
        )

        # 2. Parse Excel
        rows = self._parse_excel(file_content)
        logger.info(f"Excel parsed: {len(rows)} rows")

        # 3. Build dedup caches
        await self._build_dedup_caches()
        await self._build_plz_cache()

        # 4. Create import logs
        u_log = EtlImportLog(
            table_mapping_id=u_mapping.id,
            batch_id=batch_id,
            status="running",
            records_read=len(rows),
        )
        k_log = EtlImportLog(
            table_mapping_id=k_mapping.id,
            batch_id=batch_id,
            status="running",
            records_read=len(rows),
        )
        if not dry_run:
            self.db.add(u_log)
            self.db.add(k_log)
            await self.db.flush()

        # 5. Process rows
        stats = {
            "rows_read": len(rows),
            "unternehmen_created": 0,
            "unternehmen_updated": 0,
            "unternehmen_skipped": 0,
            "kontakte_created": 0,
            "kontakte_updated": 0,
            "kontakte_skipped": 0,
            "errors": 0,
            "error_details": [],
        }

        for i, row in enumerate(rows):
            try:
                await self._process_row(
                    row, i + 2,  # Excel row number (1-based header + 1-based data)
                    u_fields, k_fields, extid_fields,
                    source_name, stats, dry_run,
                )
            except Exception as e:
                stats["errors"] += 1
                msg = f"Zeile {i + 2}: {str(e)}"
                if len(stats["error_details"]) < 20:
                    stats["error_details"].append(msg)
                logger.warning(msg)

            # Batch commit
            if not dry_run and (i + 1) % BATCH_SIZE == 0:
                await self.db.commit()
                logger.info(f"Batch commit at row {i + 1}")

        # 6. Final commit + update logs
        if not dry_run:
            u_log.finished_at = datetime.utcnow()
            u_log.status = "success"
            u_log.records_created = stats["unternehmen_created"]
            u_log.records_updated = stats["unternehmen_updated"]
            u_log.records_skipped = stats["unternehmen_skipped"]
            u_log.records_failed = stats["errors"]

            k_log.finished_at = datetime.utcnow()
            k_log.status = "success"
            k_log.records_created = stats["kontakte_created"]
            k_log.records_updated = stats["kontakte_updated"]
            k_log.records_skipped = stats["kontakte_skipped"]

            await self.db.commit()

        stats["batch_id"] = batch_id
        stats["dry_run"] = dry_run
        return stats

    async def _process_row(
        self,
        row: dict[str, Any],
        row_num: int,
        u_fields: list[EtlFieldMapping],
        k_fields: list[EtlFieldMapping],
        extid_fields: list[tuple[str, str, str]],  # [(source_field, source_name, id_type)]
        source_name: str,
        stats: dict,
        dry_run: bool,
    ):
        """Process a single Excel row: Unternehmen + Kontakt."""
        # Apply Unternehmen field mappings
        u_data = self._apply_field_mappings(row, u_fields)

        # Resolve GeoOrt by PLZ
        if "geo_ort_id" in u_data and u_data["geo_ort_id"]:
            plz = u_data["geo_ort_id"]  # At this point it's the normalized PLZ string
            u_data["geo_ort_id"] = self._plz_cache.get(plz)

        # Skip if no meaningful data
        if not u_data.get("kurzname") and not u_data.get("firmierung"):
            stats["unternehmen_skipped"] += 1
            stats["kontakte_skipped"] += 1
            return

        # Dedup Unternehmen
        existing_id, match_method = self._dedup_unternehmen(
            u_data, row, source_name, extid_fields,
        )

        if dry_run:
            if existing_id:
                stats["unternehmen_updated"] += 1
            else:
                stats["unternehmen_created"] += 1
            # Check if kontakt would be created
            k_data = self._apply_field_mappings(row, k_fields)
            if k_data.get("vorname") and k_data.get("nachname"):
                stats["kontakte_created"] += 1
            else:
                stats["kontakte_skipped"] += 1
            return

        # Upsert Unternehmen
        unternehmen_id, u_action = await self._upsert_unternehmen(
            existing_id, u_data, u_fields,
        )
        stats[f"unternehmen_{u_action}"] += 1

        # Update dedup caches with new/updated data
        self._update_dedup_caches(unternehmen_id, u_data)

        # Save external IDs
        await self._save_external_ids(
            "unternehmen", unternehmen_id, row, extid_fields,
        )

        # Apply Kontakt field mappings
        k_data = self._apply_field_mappings(row, k_fields)

        # Skip kontakt if no name
        if not k_data.get("vorname") or not k_data.get("nachname"):
            stats["kontakte_skipped"] += 1
            return

        # Upsert Kontakt
        kontakt_id, k_action = await self._upsert_kontakt(
            unternehmen_id, k_data, k_fields,
        )
        stats[f"kontakte_{k_action}"] += 1

    # ============ Excel Parsing ============

    def _parse_excel(self, file_content: bytes) -> list[dict[str, Any]]:
        """Parse Excel file into list of dicts (column_name -> value)."""
        wb = load_workbook(BytesIO(file_content), read_only=True, data_only=True)
        ws = wb.active

        rows_iter = ws.iter_rows()
        header_row = next(rows_iter)
        headers = [
            cell.value.strip() if isinstance(cell.value, str) else str(cell.value or "")
            for cell in header_row
        ]

        result = []
        for row in rows_iter:
            row_dict = {}
            for header, cell in zip(headers, row):
                if header:
                    row_dict[header] = cell.value
            # Skip completely empty rows
            if any(v is not None and str(v).strip() for v in row_dict.values()):
                result.append(row_dict)

        wb.close()
        return result

    # ============ Config Loading ============

    async def _load_config(self, source_name: str):
        """Load ETL configuration for the given source.

        Returns: (source, u_mapping, k_mapping, u_fields, k_fields, extid_fields)
        """
        result = await self.db.execute(
            select(EtlSource)
            .where(EtlSource.name == source_name)
            .where(EtlSource.is_active.is_(True))
            .where(EtlSource.connection_type == "excel")
        )
        source = result.scalar_one_or_none()
        if not source:
            raise ValueError(f"Excel-Import-Quelle '{source_name}' nicht gefunden oder inaktiv.")

        # Load table mappings with field mappings
        result = await self.db.execute(
            select(EtlTableMapping)
            .where(EtlTableMapping.source_id == source.id)
            .where(EtlTableMapping.is_active.is_(True))
        )
        mappings = result.scalars().all()

        u_mapping = None
        k_mapping = None
        for m in mappings:
            if m.target_table == "com_unternehmen":
                u_mapping = m
            elif m.target_table == "com_kontakt":
                k_mapping = m

        if not u_mapping:
            raise ValueError(f"Kein TableMapping für com_unternehmen in '{source_name}'.")
        if not k_mapping:
            raise ValueError(f"Kein TableMapping für com_kontakt in '{source_name}'.")

        # Load field mappings
        u_fields_result = await self.db.execute(
            select(EtlFieldMapping)
            .where(EtlFieldMapping.table_mapping_id == u_mapping.id)
        )
        k_fields_result = await self.db.execute(
            select(EtlFieldMapping)
            .where(EtlFieldMapping.table_mapping_id == k_mapping.id)
        )

        u_fields_all = list(u_fields_result.scalars().all())
        k_fields_all = list(k_fields_result.scalars().all())

        # Separate external_id fields from regular fields
        u_fields = []
        extid_fields = []
        for f in u_fields_all:
            if f.transform and f.transform.startswith("external_id:"):
                # Parse "external_id:smartmail.subscriber_id"
                parts = f.transform.split(":", 1)[1]
                src_name, id_type = parts.split(".", 1)
                extid_fields.append((f.source_field, src_name, id_type))
            else:
                u_fields.append(f)

        return source, u_mapping, k_mapping, u_fields, k_fields_all, extid_fields

    # ============ Field Mapping ============

    def _apply_field_mappings(
        self,
        row: dict[str, Any],
        field_mappings: list[EtlFieldMapping],
    ) -> dict[str, Any]:
        """Apply all field mappings + transformations to a single row."""
        result = {}
        for fm in field_mappings:
            value = row.get(fm.source_field)

            # Coerce to string (openpyxl returns int/float for numeric cells)
            if value is not None and not isinstance(value, str):
                value = str(value).strip()

            # Apply default if value is None/empty
            if value is None or not value.strip():
                if fm.default_value is not None:
                    value = fm.default_value
                elif fm.is_required:
                    continue  # Skip required fields with no value
                else:
                    result[fm.target_field] = None
                    continue

            # Apply transformation
            if fm.transform and fm.transform in TRANSFORMS:
                value = TRANSFORMS[fm.transform](value)
            elif fm.transform and fm.transform.startswith("fk_lookup:"):
                pass  # Handled separately if needed

            result[fm.target_field] = value

        return result

    # ============ Dedup Caches ============

    async def _build_dedup_caches(self):
        """Pre-load all existing Unternehmen into lookup caches."""
        # Load all non-deleted Unternehmen
        result = await self.db.execute(
            select(
                ComUnternehmen.id,
                ComUnternehmen.email,
                ComUnternehmen.website,
                ComUnternehmen.telefon,
                ComUnternehmen.firmierung,
                ComUnternehmen.strasse,
            ).where(ComUnternehmen.geloescht_am.is_(None))
        )
        for row in result.all():
            uid = str(row.id)
            if row.email:
                key = row.email.strip().lower()
                if key:
                    self._email_cache[key] = uid
            if row.website:
                key = _normalize_url_for_cache(row.website)
                if key:
                    self._url_cache[key] = uid
            if row.telefon:
                key = _normalize_phone_for_cache(row.telefon)
                if key:
                    self._phone_cache[key] = uid
            if row.firmierung:
                key = row.firmierung.strip().lower()
                if key:
                    self._name_cache[key] = uid

        # Load all external IDs
        result = await self.db.execute(
            select(ComExternalId).where(ComExternalId.entity_type == "unternehmen")
        )
        for eid in result.scalars().all():
            cache_key = f"{eid.source_name}:{eid.id_type}:{eid.external_value}"
            self._extid_cache[cache_key] = str(eid.entity_id)
            entity_key = f"{eid.entity_type}:{eid.entity_id}:{eid.source_name}:{eid.id_type}"
            self._entity_extid_set.add(entity_key)

        logger.info(
            f"Dedup caches loaded: {len(self._email_cache)} emails, "
            f"{len(self._url_cache)} urls, {len(self._phone_cache)} phones, "
            f"{len(self._name_cache)} names, {len(self._extid_cache)} external IDs"
        )

    async def _build_plz_cache(self):
        """Pre-load PLZ -> GeoOrt.id mapping."""
        result = await self.db.execute(
            text("""
                SELECT plz, id, ist_hauptort
                FROM geo_ort
                WHERE plz IS NOT NULL AND plz != ''
                ORDER BY ist_hauptort DESC
            """)
        )
        for row in result.all():
            plz = str(row[0]).strip().zfill(5)
            ort_id = str(row[1])
            # First match wins (ist_hauptort=True first due to ORDER BY)
            if plz not in self._plz_cache:
                self._plz_cache[plz] = ort_id

        logger.info(f"PLZ cache loaded: {len(self._plz_cache)} entries")

    def _update_dedup_caches(self, unternehmen_id: str, u_data: dict):
        """Update caches after creating/updating an Unternehmen."""
        uid = unternehmen_id
        if u_data.get("email"):
            self._email_cache[u_data["email"].strip().lower()] = uid
        if u_data.get("website"):
            key = _normalize_url_for_cache(u_data["website"])
            if key:
                self._url_cache[key] = uid
        if u_data.get("telefon"):
            key = _normalize_phone_for_cache(u_data["telefon"])
            if key:
                self._phone_cache[key] = uid
        if u_data.get("firmierung"):
            self._name_cache[u_data["firmierung"].strip().lower()] = uid

    # ============ Dedup Logic ============

    def _dedup_unternehmen(
        self,
        u_data: dict,
        source_row: dict,
        source_name: str,
        extid_fields: list[tuple[str, str, str]],
    ) -> tuple[str | None, str | None]:
        """
        Multi-stage deduplication cascade.
        Returns: (existing_unternehmen_id, match_method)
        """
        # Stage 1: External ID match
        for src_field, ext_source, ext_type in extid_fields:
            ext_val = source_row.get(src_field)
            if ext_val is not None and str(ext_val).strip():
                cache_key = f"{ext_source}:{ext_type}:{str(ext_val).strip()}"
                if cache_key in self._extid_cache:
                    return self._extid_cache[cache_key], "external_id"

        # Stage 2: Email match
        if u_data.get("email"):
            key = u_data["email"].strip().lower()
            if key in self._email_cache:
                return self._email_cache[key], "email"

        # Stage 3: Website match
        if u_data.get("website"):
            key = _normalize_url_for_cache(u_data["website"])
            if key and key in self._url_cache:
                return self._url_cache[key], "website"

        # Stage 4: Phone match
        if u_data.get("telefon"):
            key = _normalize_phone_for_cache(u_data["telefon"])
            if key and key in self._phone_cache:
                return self._phone_cache[key], "telefon"

        # Stage 5: Address match (PLZ + Strasse)
        # Not implemented in cache yet — would need composite key
        # This is a V2 enhancement

        # Stage 6: Firmierung match
        if u_data.get("firmierung"):
            key = u_data["firmierung"].strip().lower()
            if key in self._name_cache:
                return self._name_cache[key], "firmierung"

        return None, None

    # ============ Upsert Logic ============

    async def _upsert_unternehmen(
        self,
        existing_id: str | None,
        u_data: dict[str, Any],
        field_mappings: list[EtlFieldMapping],
    ) -> tuple[str, str]:
        """Create or update Unternehmen respecting update_rules.

        Returns: (unternehmen_id, "created" | "updated")
        """
        # Build update_rule map: target_field -> rule
        rules = {}
        for fm in field_mappings:
            rules[fm.target_field] = fm.update_rule or "always"

        if existing_id:
            # UPDATE existing
            result = await self.db.execute(
                select(ComUnternehmen).where(ComUnternehmen.id == existing_id)
            )
            unternehmen = result.scalar_one_or_none()
            if not unternehmen:
                # ID from cache but not in DB — create new
                return await self._create_unternehmen(u_data), "created"

            updated = False
            for field, value in u_data.items():
                if field in ("id", "erstellt_am", "aktualisiert_am", "geloescht_am"):
                    continue
                rule = rules.get(field, "always")
                current_value = getattr(unternehmen, field, None)

                if rule == "never":
                    continue
                elif rule == "if_empty":
                    if current_value is not None and str(current_value).strip():
                        continue

                if value != current_value:
                    setattr(unternehmen, field, value)
                    updated = True

            if updated:
                unternehmen.aktualisiert_am = datetime.utcnow()
                await self.db.flush()

            return str(unternehmen.id), "updated"
        else:
            # CREATE new
            new_id = await self._create_unternehmen(u_data)
            return new_id, "created"

    async def _create_unternehmen(self, u_data: dict[str, Any]) -> str:
        """Create a new Unternehmen record."""
        new_id = generate_uuid()
        unternehmen = ComUnternehmen(id=new_id, **u_data)
        self.db.add(unternehmen)
        await self.db.flush()
        return str(new_id)

    async def _upsert_kontakt(
        self,
        unternehmen_id: str,
        k_data: dict[str, Any],
        field_mappings: list[EtlFieldMapping],
    ) -> tuple[str, str]:
        """Create or update Kontakt. Dedup by email within Unternehmen.

        Returns: (kontakt_id, "created" | "updated")
        """
        # Try to find existing kontakt by email within this Unternehmen
        existing_kontakt = None
        if k_data.get("email"):
            result = await self.db.execute(
                select(ComKontakt)
                .where(ComKontakt.unternehmen_id == unternehmen_id)
                .where(ComKontakt.email == k_data["email"])
                .where(ComKontakt.geloescht_am.is_(None))
            )
            existing_kontakt = result.scalars().first()

        if existing_kontakt:
            # Update existing kontakt
            rules = {}
            for fm in field_mappings:
                rules[fm.target_field] = fm.update_rule or "always"

            updated = False
            for field, value in k_data.items():
                if field in ("id", "unternehmen_id", "erstellt_am", "aktualisiert_am"):
                    continue
                rule = rules.get(field, "always")
                current = getattr(existing_kontakt, field, None)

                if rule == "never":
                    continue
                elif rule == "if_empty":
                    if current is not None and str(current).strip():
                        continue

                if value != current:
                    setattr(existing_kontakt, field, value)
                    updated = True

            if updated:
                existing_kontakt.aktualisiert_am = datetime.utcnow()
                await self.db.flush()

            return str(existing_kontakt.id), "updated"
        else:
            # Create new kontakt
            new_id = generate_uuid()
            # Check if this is the first kontakt for the Unternehmen
            count_result = await self.db.execute(
                select(ComKontakt)
                .where(ComKontakt.unternehmen_id == unternehmen_id)
                .where(ComKontakt.geloescht_am.is_(None))
            )
            is_first = count_result.scalar_one_or_none() is None

            kontakt = ComKontakt(
                id=new_id,
                unternehmen_id=unternehmen_id,
                ist_hauptkontakt=is_first,
                **k_data,
            )
            self.db.add(kontakt)
            await self.db.flush()
            return str(new_id), "created"

    # ============ External IDs ============

    async def _save_external_ids(
        self,
        entity_type: str,
        entity_id: str,
        source_row: dict[str, Any],
        extid_fields: list[tuple[str, str, str]],
    ):
        """Save external IDs from source row to com_external_id."""
        for src_field, ext_source, ext_type in extid_fields:
            ext_val = source_row.get(src_field)
            if ext_val is None or not str(ext_val).strip():
                continue

            ext_val_str = str(ext_val).strip()
            cache_key = f"{ext_source}:{ext_type}:{ext_val_str}"

            # Check if this exact value already exists
            if cache_key in self._extid_cache:
                continue

            # Check if entity already has an external_id for this source+type
            entity_key = f"{entity_type}:{entity_id}:{ext_source}:{ext_type}"
            if entity_key in self._entity_extid_set:
                continue

            # Create new external ID
            new_extid = ComExternalId(
                entity_type=entity_type,
                entity_id=entity_id,
                source_name=ext_source,
                id_type=ext_type,
                external_value=ext_val_str,
            )
            self.db.add(new_extid)
            self._extid_cache[cache_key] = entity_id
            self._entity_extid_set.add(entity_key)


# ============ Helper Functions ============

def _normalize_url_for_cache(url: str) -> str | None:
    """Normalize URL for cache lookup."""
    import re
    if not url or not url.strip():
        return None
    url = url.strip().lower()
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    url = url.rstrip('/')
    return url if url else None


def _normalize_phone_for_cache(phone: str) -> str | None:
    """Normalize phone for cache lookup."""
    import re
    if not phone or not phone.strip():
        return None
    p = phone.strip()
    p = re.sub(r'^\+49\s*', '0', p)
    p = re.sub(r'^0049\s*', '0', p)
    p = re.sub(r'[^\d]', '', p)
    return p if p else None
