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
    """Extract Anrede: 'Sehr geehrter Herr' or 'Herr Jan Müller' -> 'Herr'."""
    if not isinstance(value, str) or not value.strip():
        return value
    val = value.strip()
    if 'Herr' in val:
        return 'Herr'
    if 'Frau' in val:
        return 'Frau'
    return val


def _extract_plz(value: Any) -> Any:
    """Extract PLZ from combined 'PLZ Ort': '39619 Arendsee' -> '39619'."""
    if value is None:
        return None
    val = str(value).strip()
    if not val:
        return None
    match = re.match(r'^(\d{4,5})\s+', val)
    if match:
        return match.group(1).zfill(5)
    # Fallback: try pure digits
    digits = re.sub(r'[^\d]', '', val)
    return digits.zfill(5) if digits else None


def _extract_vorname(value: Any) -> Any:
    """Extract Vorname from 'Anrede Vorname Nachname': 'Herr Jan Müller' -> 'Jan'."""
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split()
    # Skip Anrede (Herr/Frau) at the beginning
    if parts and parts[0] in ('Herr', 'Frau'):
        parts = parts[1:]
    return parts[0].strip() if len(parts) >= 2 else None


def _extract_nachname(value: Any) -> Any:
    """Extract Nachname from 'Anrede Vorname Nachname': 'Herr Jan Müller' -> 'Müller'."""
    if not isinstance(value, str) or not value.strip():
        return None
    parts = value.strip().split()
    # Skip Anrede (Herr/Frau) at the beginning
    if parts and parts[0] in ('Herr', 'Frau'):
        parts = parts[1:]
    return ' '.join(parts[1:]).strip() if len(parts) >= 2 else None


# ============ New Simple Transforms (Märklin Import) ============

# Legal suffixes that should keep their casing in title_case
_LEGAL_SUFFIXES = {
    "gmbh", "ag", "kg", "ohg", "ug", "gbr", "co.", "e.k.", "e.v.",
    "s.a.", "s.r.l.", "ltd.", "inc.", "b.v.", "n.v.", "s.a.s.",
    "gmbh", "kgaa",
}
_LEGAL_UPPER = {s.upper(): s for s in [
    "GmbH", "AG", "KG", "OHG", "UG", "GbR", "Co.", "e.K.", "e.V.",
    "S.A.", "S.r.l.", "Ltd.", "Inc.", "B.V.", "N.V.", "S.A.S.",
    "GmbH", "KGaA",
]}


def _smart_title_case(value: Any) -> Any:
    """Convert ALL-CAPS strings to Title Case, preserving legal suffixes."""
    if not isinstance(value, str) or not value.strip():
        return value
    v = value.strip()
    if v != v.upper():
        return v  # Not all-caps, leave as-is
    # Apply title() then fix legal suffixes
    result = v.title()
    for upper_form, correct_form in _LEGAL_UPPER.items():
        result = result.replace(upper_form.title(), correct_form)
    return result


def _strip_star(value: Any) -> Any:
    """Remove leading stars: '*CATYBA' -> 'CATYBA'."""
    if isinstance(value, str):
        return value.lstrip("*").strip()
    return value


def _strip_star_title_case(value: Any) -> Any:
    """Strip leading stars, then apply smart_title_case."""
    return _smart_title_case(_strip_star(value))


def _map_sprache(value: Any) -> Any:
    """Map single-char language code to ISO 639-1: D->de, E->en, etc."""
    if not isinstance(value, str) or not value.strip():
        return value
    mapping = {"D": "de", "d": "de", "E": "en", "e": "en",
               "F": "fr", "f": "fr", "I": "it", "i": "it",
               "N": "nl", "n": "nl"}
    return mapping.get(value.strip(), value.strip().lower())


def _map_loeschkennzeichen(value: Any) -> Any:
    """Map deletion flag to status: L/*->geschlossen, else->aktiv."""
    if value and str(value).strip() in ("L", "*"):
        return "geschlossen"
    return "aktiv"


def _map_store_typ(value: Any) -> Any:
    """Map store type code to label."""
    if not value:
        return "standard"
    mapping = {
        "1": "maerklin_store", "2": "shop_in_shop",
        "3": "wandloesung", "99": "standard",
    }
    return mapping.get(str(value).strip(), "standard")


def _invert_x_flag(value: Any) -> Any:
    """Invert X flag: X->False (keine Anzeige), empty->True."""
    return not (value and str(value).strip().upper() == "X")


def _x_to_bool(value: Any) -> Any:
    """Convert X flag to bool: X->True, empty->False."""
    return bool(value and str(value).strip().upper() == "X")


def _validate_ean(value: Any) -> Any:
    """Validate EAN/GTIN checksum (GS1 standard). Returns value if valid, None if invalid."""
    if not value:
        return value
    ean = str(value).strip().replace(" ", "")
    if not ean.isdigit() or len(ean) not in (8, 12, 13, 14):
        return None
    digits = [int(d) for d in ean]
    checksum = sum(d * (3 if i % 2 else 1) for i, d in enumerate(digits[:-1]))
    expected = (10 - checksum % 10) % 10
    return ean if digits[-1] == expected else None


def _normalize_ean(value: Any) -> Any:
    """Normalize EAN to 13 digits (pad EAN-8 with leading zeros)."""
    if not value:
        return value
    ean = str(value).strip().replace(" ", "")
    if not ean.isdigit():
        return value
    if len(ean) == 8:
        return ean.rjust(13, "0")
    return ean


# ============ Row-Context Transforms ============
# Signature: def transform(value, *, row: dict, params: str | None) -> Any

# Rechtsform-Marker that indicate a company (not a sole proprietor)
_COMPANY_MARKERS = {
    "gmbh", "ag", "kg", "ohg", "ug", "gbr", "co.", "e.k.", "e.v.",
    "ltd", "inc", "s.a.", "s.r.l.", "b.v.", "n.v.", "s.a.s.",
    "kgaa", "co.kg", "co. kg", "& co",
}

# Inhaber-Marker in Name2
_INHABER_MARKERS = {"inh.", "inh ", "inhaber", "inhaberin"}


def _is_person_name(text: str) -> bool:
    """Heuristic: text looks like a person name (2-3 words, no company markers)."""
    if not text or not text.strip():
        return False
    words = text.strip().split()
    if len(words) < 2 or len(words) > 4:
        return False
    lower = text.lower()
    # Check for company markers
    for marker in _COMPANY_MARKERS:
        if marker in lower:
            return False
    # Check for special chars typical of company names
    if any(c in text for c in "&+/"):
        return False
    return True


def _detect_inhaber(name1: str | None, name2: str | None, land: str | None) -> dict | None:
    """Detect owner info from Name1+Name2.

    Returns: {"vorname": ..., "nachname": ..., "typ": ...} or None.
    Only applies for DE/AT/CH.
    """
    if not name2 or not name2.strip():
        return None

    # Only DACH countries
    if land and land.strip().upper() not in ("DE", "AT", "CH", "D", "A"):
        return None

    name2_stripped = name2.strip()
    lower2 = name2_stripped.lower()

    # 1. Explicit Inhaber marker
    for marker in _INHABER_MARKERS:
        if marker in lower2:
            # Extract name after marker
            idx = lower2.index(marker) + len(marker)
            rest = name2_stripped[idx:].strip()
            parts = rest.split()
            if len(parts) >= 2:
                return {
                    "vorname": parts[0],
                    "nachname": " ".join(parts[1:]),
                    "typ": "Inhaber",
                }
            elif len(parts) == 1:
                return {"vorname": "", "nachname": parts[0], "typ": "Inhaber"}
            return None

    # 2. Heuristic: Name2 is a person name AND Name1 has no company suffix
    if name1:
        lower1 = name1.lower()
        has_company_suffix = any(m in lower1 for m in _COMPANY_MARKERS)
        if not has_company_suffix and _is_person_name(name2_stripped):
            parts = name2_stripped.split()
            return {
                "vorname": parts[0],
                "nachname": " ".join(parts[1:]),
                "typ": "Inhaber",
            }

    return None


def _build_firmierung(value: Any, *, row: dict, params: str | None) -> Any:
    """Build proper company name from Name1 + Name2.

    Params: Name of the Name2 field (e.g., 'Name2').
    """
    name1 = _strip_star_title_case(value)
    if not name1 or not str(name1).strip():
        return None

    name2_field = params or "Name2"
    name2 = row.get(name2_field)
    if not name2 or not str(name2).strip():
        return str(name1).strip()

    name2 = str(name2).strip()
    land = row.get("Land")
    inhaber = _detect_inhaber(str(name1), name2, str(land) if land else None)

    if inhaber and inhaber.get("vorname"):
        return f"{str(name1).strip()} - Inh. {inhaber['vorname']} {inhaber['nachname']}"
    elif inhaber:
        return f"{str(name1).strip()} - Inh. {inhaber['nachname']}"
    else:
        # Name2 is likely a secondary company name
        name2_clean = _smart_title_case(name2) if name2 == name2.upper() else name2
        return f"{str(name1).strip()} {name2_clean}".strip()


def _detect_inhaber_vorname(value: Any, *, row: dict, params: str | None) -> Any:
    """Extract owner first name from Name2. Params: Name1 field name."""
    name1_field = params or "Name1"
    name1 = row.get(name1_field)
    land = row.get("Land")
    inhaber = _detect_inhaber(
        str(name1) if name1 else None,
        str(value) if value else None,
        str(land) if land else None,
    )
    return inhaber["vorname"] if inhaber else None


def _detect_inhaber_nachname(value: Any, *, row: dict, params: str | None) -> Any:
    """Extract owner last name from Name2. Params: Name1 field name."""
    name1_field = params or "Name1"
    name1 = row.get(name1_field)
    land = row.get("Land")
    inhaber = _detect_inhaber(
        str(name1) if name1 else None,
        str(value) if value else None,
        str(land) if land else None,
    )
    return inhaber["nachname"] if inhaber else None


def _detect_inhaber_typ(value: Any, *, row: dict, params: str | None) -> Any:
    """Detect contact type from Name2. Returns 'Inhaber' or None."""
    name1_field = params or "Name1"
    name1 = row.get(name1_field)
    land = row.get("Land")
    inhaber = _detect_inhaber(
        str(name1) if name1 else None,
        str(value) if value else None,
        str(land) if land else None,
    )
    return inhaber["typ"] if inhaber else None


def _normalize_phone_e164(value: Any, *, row: dict, params: str | None) -> Any:
    """Normalize phone number to E.164 format using country from row.

    Params: Name of the country field (e.g., 'Land').
    """
    if not isinstance(value, str) or not value.strip():
        return value
    try:
        import phonenumbers
    except ImportError:
        return _normalize_phone(value)

    country_field = params or "Land"
    country_raw = row.get(country_field)
    country = str(country_raw).strip().upper() if country_raw else "DE"
    # Map single-char codes
    country_map = {"D": "DE", "A": "AT", "F": "FR", "I": "IT", "N": "NL"}
    country = country_map.get(country, country)

    try:
        parsed = phonenumbers.parse(value.strip(), country)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(
                parsed, phonenumbers.PhoneNumberFormat.E164
            )
    except Exception:
        pass

    # Fallback to simple normalization
    return _normalize_phone(value)


def _split_street_name_dach(value: Any, *, row: dict, params: str | None) -> Any:
    """Split street name — only for DACH countries. Returns None otherwise."""
    country_field = params or "Land"
    country = row.get(country_field)
    c = str(country).strip().upper() if country else ""
    dach = {"DE", "AT", "CH", "NL", "D", "A"}
    if c in dach:
        return _split_street_name(value)
    return None


def _split_street_hausnr_dach(value: Any, *, row: dict, params: str | None) -> Any:
    """Split house number — only for DACH countries. Returns None otherwise."""
    country_field = params or "Land"
    country = row.get(country_field)
    c = str(country).strip().upper() if country else ""
    dach = {"DE", "AT", "CH", "NL", "D", "A"}
    if c in dach:
        return _split_street_hausnr(value)
    return None


def _map_bonitaet_score(value: Any, *, row: dict, params: str | None) -> Any:
    """Map credit/order block flags to score. Returns None if no blocks.

    Value: Kreditsperre flag, Params: Auftragssperre field name.
    """
    kredit = bool(value and str(value).strip().upper() in ("X", "1"))
    auftrags_field = params
    auftrags_val = row.get(auftrags_field) if auftrags_field else None
    auftrags = bool(auftrags_val and str(auftrags_val).strip().upper() in ("X", "1"))

    if kredit and auftrags:
        return 5
    if auftrags:
        return 4
    if kredit:
        return 3
    return None  # No entry


# ============ Registries ============

# Standard transforms: value -> value
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
    "extract_plz": _extract_plz,
    "extract_vorname": _extract_vorname,
    "extract_nachname": _extract_nachname,
    # Märklin import transforms
    "smart_title_case": _smart_title_case,
    "strip_star": _strip_star,
    "strip_star_title_case": _strip_star_title_case,
    "map_sprache": _map_sprache,
    "map_loeschkennzeichen": _map_loeschkennzeichen,
    "map_store_typ": _map_store_typ,
    "invert_x_flag": _invert_x_flag,
    "x_to_bool": _x_to_bool,
    # Produktdaten transforms
    "validate_ean": _validate_ean,
    "normalize_ean": _normalize_ean,
    "mwst_code": lambda v: {"1": 19.0, "2": 7.0, "3": 0.0}.get(str(v).strip(), None) if v else None,
    "aktiv_to_status": lambda v: "AKT" if str(v).strip().lower() in ("true", "1", "ja", "yes") else "AUS",
    "rabatt_to_bool": lambda v: str(v).strip() == "1" if v else False,
}

# Row-context transforms: (value, row, params) -> value
# Used when a transform needs access to other columns in the same row.
# Syntax in FieldMapping: "transform_name:param" (param is optional).
ROW_TRANSFORMS: dict[str, Callable] = {
    "build_firmierung": _build_firmierung,
    "detect_inhaber_vorname": _detect_inhaber_vorname,
    "detect_inhaber_nachname": _detect_inhaber_nachname,
    "detect_inhaber_typ": _detect_inhaber_typ,
    "normalize_phone_e164": _normalize_phone_e164,
    "split_street_name_dach": _split_street_name_dach,
    "split_street_hausnr_dach": _split_street_hausnr_dach,
    "map_bonitaet_score": _map_bonitaet_score,
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

    async def fk_lookup(
        self,
        value: Any,
        table: str,
        field: str,
        fk_caches: dict[str, dict[Any, str]],
    ) -> str | None:
        """
        Lookup a FK value. Returns None if not found (no auto-create).

        Args:
            value: The lookup value (e.g., "Busch GmbH & Co. KG")
            table: Target table (e.g., "com_unternehmen")
            field: Lookup field (e.g., "firmierung")
            fk_caches: Shared FK caches dict
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return None

        cache_key = f"{table}.{field}"
        cache = fk_caches.get(cache_key, {})
        if value in cache:
            return cache[value]

        query = text(f"SELECT id FROM {table} WHERE {field} = :val LIMIT 1")
        result = await self.db.execute(query, {"val": value})
        row = result.fetchone()
        if row:
            record_id = str(row[0])
            fk_caches.setdefault(cache_key, {})[value] = record_id
            return record_id

        return None

    async def fk_lookup_or_create(
        self,
        value: Any,
        table: str,
        field: str,
        fk_caches: dict[str, dict[Any, str]],
    ) -> str | None:
        """
        Lookup a FK value in the cache, create the record if not found.

        Args:
            value: The lookup value (e.g., "FEDES")
            table: Target table (e.g., "com_organisation")
            field: Lookup field (e.g., "kurzname")
            fk_caches: Shared FK caches dict (will be updated on create)

        Returns:
            ID of the found or newly created record, or None if value is empty.
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            return None

        cache_key = f"{table}.{field}"

        # 1. Cache lookup
        cache = fk_caches.get(cache_key, {})
        if value in cache:
            return cache[value]

        # 2. DB lookup (cache might be stale)
        query = text(f"SELECT id FROM {table} WHERE {field} = :val LIMIT 1")
        result = await self.db.execute(query, {"val": value})
        row = result.fetchone()
        if row:
            record_id = str(row[0])
            fk_caches.setdefault(cache_key, {})[value] = record_id
            return record_id

        # 3. Create new record
        from app.models.geo import generate_uuid
        new_id = str(generate_uuid())
        now = datetime.utcnow()
        insert_query = text(
            f"INSERT INTO {table} (id, {field}, erstellt_am, aktualisiert_am) "
            f"VALUES (:id, :val, :now, :now)"
        )
        await self.db.execute(insert_query, {"id": new_id, "val": value, "now": now})
        await self.db.flush()

        # Update cache
        fk_caches.setdefault(cache_key, {})[value] = new_id
        return new_id

    def apply_transform(
        self,
        value: Any,
        transform: str | None,
        fk_caches: dict[str, dict[Any, str]] | None = None,
        ref_context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Apply a transformation to a value.

        Args:
            value: The value to transform
            transform: Transformation name or "fk_lookup:table.field" or "ref_current:field"
            fk_caches: Pre-built FK lookup caches
            ref_context: Current record context for ref_current transforms

        Returns:
            Transformed value
        """
        if transform is None:
            return value

        # Handle ref_current — references a field from the current primary record
        if transform.startswith("ref_current:"):
            if ref_context is None:
                return None
            field = transform.split(":", 1)[1]
            return ref_context.get(field)

        # Handle FK lookup transformation
        if transform.startswith("fk_lookup_or_create:") or transform.startswith("fk_lookup:"):
            if fk_caches is None:
                return None

            # Parse "fk_lookup:geo_ort.legacy_id" or "fk_lookup_or_create:com_organisation.kurzname"
            prefix_len = len(transform.split(":")[0]) + 1  # "fk_lookup:" or "fk_lookup_or_create:"
            lookup_spec = transform[prefix_len:]
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
        return list(TRANSFORMS.keys()) + [
            f"{name}:<param>" for name in ROW_TRANSFORMS.keys()
        ] + [
            "fk_lookup:<table>.<field>",
            "fk_lookup_or_create:<table>.<field>",
            "ref_current:<field>",
            "business_id:<typ>",
        ]
