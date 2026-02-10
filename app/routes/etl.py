"""
API Routes for ETL (Extract-Transform-Load) configuration.

All endpoints are Superadmin only.
Provides CRUD operations for Sources, TableMappings, and FieldMappings,
plus schema discovery and bulk operations for the visual mapping editor.
"""
import json

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.geo import Base
from app.models.partner import ApiPartner
from app.models.etl import EtlTableMapping, EtlFieldMapping
from app.services.etl import EtlService
from app.schemas.etl import (
    EtlSourceCreate,
    EtlSourceUpdate,
    EtlSourceResponse,
    EtlSourceWithMappings,
    EtlSourceList,
    EtlTableMappingCreate,
    EtlTableMappingUpdate,
    EtlTableMappingResponse,
    EtlTableMappingWithFields,
    EtlTableMappingList,
    EtlFieldMappingCreate,
    EtlFieldMappingUpdate,
    EtlFieldMappingResponse,
    EtlFieldMappingList,
    EtlImportLogResponse,
    EtlImportLogList,
    BulkFieldMappingPayload,
    BulkFieldMappingResponse,
    TableColumnInfo,
    TableSchemaResponse,
)

# Tables available for ETL mapping (security whitelist)
ALLOWED_ETL_TABLES = {
    'com_unternehmen', 'com_kontakt', 'com_organisation',
    'com_unternehmen_organisation', 'com_external_id',
    'geo_land', 'geo_bundesland', 'geo_kreis', 'geo_ort', 'geo_ortsteil',
}

router = APIRouter(prefix="/etl", tags=["ETL"])


# ============ EtlSource Endpoints ============

@router.get("/sources", response_model=EtlSourceList)
async def list_sources(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller ETL-Quellen (nur Superadmin).
    """
    service = EtlService(db)
    return await service.get_sources(skip=skip, limit=limit)


@router.get("/sources/{source_id}", response_model=EtlSourceWithMappings)
async def get_source(
    source_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelne ETL-Quelle mit Tabellen-Mappings abrufen (nur Superadmin).
    """
    service = EtlService(db)
    source = await service.get_source_by_id(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return source


@router.get("/sources/name/{name}", response_model=EtlSourceWithMappings)
async def get_source_by_name(
    name: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    ETL-Quelle nach Name abrufen (nur Superadmin).
    """
    service = EtlService(db)
    source = await service.get_source_by_name(name)
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return source


@router.post("/sources", response_model=EtlSourceResponse, status_code=201)
async def create_source(
    data: EtlSourceCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neue ETL-Quelle anlegen (nur Superadmin).
    """
    service = EtlService(db)

    # Check if name already exists
    existing = await service.get_source_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Quelle mit diesem Namen existiert bereits")

    return await service.create_source(data)


@router.patch("/sources/{source_id}", response_model=EtlSourceResponse)
async def update_source(
    source_id: str,
    data: EtlSourceUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    ETL-Quelle aktualisieren (nur Superadmin).
    """
    service = EtlService(db)
    source = await service.update_source(source_id, data)
    if not source:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")
    return source


@router.delete("/sources/{source_id}", status_code=204)
async def delete_source(
    source_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    ETL-Quelle löschen (nur Superadmin).

    Löscht auch alle zugehörigen Tabellen- und Feld-Mappings.
    """
    service = EtlService(db)
    if not await service.delete_source(source_id):
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")


# ============ EtlTableMapping Endpoints ============

@router.get("/table-mappings", response_model=EtlTableMappingList)
async def list_table_mappings(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    source_id: str | None = Query(None, description="Filter nach Quell-ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Tabellen-Mappings (nur Superadmin).
    """
    service = EtlService(db)
    return await service.get_table_mappings(source_id=source_id, skip=skip, limit=limit)


@router.get("/table-mappings/{mapping_id}", response_model=EtlTableMappingWithFields)
async def get_table_mapping(
    mapping_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnes Tabellen-Mapping mit Feld-Mappings abrufen (nur Superadmin).
    """
    service = EtlService(db)
    mapping = await service.get_table_mapping_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Tabellen-Mapping nicht gefunden")
    return mapping


@router.post("/table-mappings", response_model=EtlTableMappingResponse, status_code=201)
async def create_table_mapping(
    data: EtlTableMappingCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neues Tabellen-Mapping anlegen (nur Superadmin).
    """
    service = EtlService(db)

    # Check if source exists
    source = await service.get_source_by_id(data.source_id)
    if not source:
        raise HTTPException(status_code=400, detail="Quell-ID nicht gefunden")

    # Check if mapping already exists
    existing = await service.get_table_mapping_by_tables(
        data.source_id, data.source_table, data.target_table
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Mapping für diese Quell-/Ziel-Tabellen existiert bereits"
        )

    return await service.create_table_mapping(data)


@router.patch("/table-mappings/{mapping_id}", response_model=EtlTableMappingResponse)
async def update_table_mapping(
    mapping_id: str,
    data: EtlTableMappingUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Tabellen-Mapping aktualisieren (nur Superadmin).
    """
    service = EtlService(db)
    mapping = await service.update_table_mapping(mapping_id, data)
    if not mapping:
        raise HTTPException(status_code=404, detail="Tabellen-Mapping nicht gefunden")
    return mapping


@router.delete("/table-mappings/{mapping_id}", status_code=204)
async def delete_table_mapping(
    mapping_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Tabellen-Mapping löschen (nur Superadmin).

    Löscht auch alle zugehörigen Feld-Mappings.
    """
    service = EtlService(db)
    if not await service.delete_table_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="Tabellen-Mapping nicht gefunden")


# ============ EtlFieldMapping Endpoints ============

@router.get("/field-mappings", response_model=EtlFieldMappingList)
async def list_field_mappings(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    table_mapping_id: str | None = Query(None, description="Filter nach Tabellen-Mapping-ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Feld-Mappings (nur Superadmin).
    """
    service = EtlService(db)
    return await service.get_field_mappings(table_mapping_id=table_mapping_id, skip=skip, limit=limit)


@router.get("/field-mappings/{mapping_id}", response_model=EtlFieldMappingResponse)
async def get_field_mapping(
    mapping_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Einzelnes Feld-Mapping abrufen (nur Superadmin).
    """
    service = EtlService(db)
    mapping = await service.get_field_mapping_by_id(mapping_id)
    if not mapping:
        raise HTTPException(status_code=404, detail="Feld-Mapping nicht gefunden")
    return mapping


@router.post("/field-mappings", response_model=EtlFieldMappingResponse, status_code=201)
async def create_field_mapping(
    data: EtlFieldMappingCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neues Feld-Mapping anlegen (nur Superadmin).
    """
    service = EtlService(db)

    # Check if table mapping exists
    table_mapping = await service.get_table_mapping_by_id(data.table_mapping_id)
    if not table_mapping:
        raise HTTPException(status_code=400, detail="Tabellen-Mapping-ID nicht gefunden")

    return await service.create_field_mapping(data)


@router.patch("/field-mappings/{mapping_id}", response_model=EtlFieldMappingResponse)
async def update_field_mapping(
    mapping_id: str,
    data: EtlFieldMappingUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Feld-Mapping aktualisieren (nur Superadmin).
    """
    service = EtlService(db)
    mapping = await service.update_field_mapping(mapping_id, data)
    if not mapping:
        raise HTTPException(status_code=404, detail="Feld-Mapping nicht gefunden")
    return mapping


@router.delete("/field-mappings/{mapping_id}", status_code=204)
async def delete_field_mapping(
    mapping_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Feld-Mapping löschen (nur Superadmin).
    """
    service = EtlService(db)
    if not await service.delete_field_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="Feld-Mapping nicht gefunden")


# ============ EtlImportLog Endpoints ============

@router.get("/import-logs", response_model=EtlImportLogList)
async def list_import_logs(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    table_mapping_id: str | None = Query(None, description="Filter nach Tabellen-Mapping-ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """
    Liste aller Import-Logs (nur Superadmin).

    Sortiert nach Startzeit (neueste zuerst).
    """
    service = EtlService(db)
    return await service.get_import_logs(table_mapping_id=table_mapping_id, skip=skip, limit=limit)


# ============ Bulk Operations (Visual Editor) ============

@router.put(
    "/table-mappings/{mapping_id}/field-mappings/bulk",
    response_model=BulkFieldMappingResponse,
)
async def bulk_replace_field_mappings(
    mapping_id: str,
    payload: BulkFieldMappingPayload,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Alle Feld-Mappings eines Tabellen-Mappings ersetzen (nur Superadmin).

    Idempotente Operation für den visuellen Mapping-Editor:
    1. Löscht alle bestehenden Feld-Mappings
    2. Erstellt neue Feld-Mappings aus dem Payload
    3. Speichert optional den Drawflow-Layout-State
    """
    service = EtlService(db)
    tm = await service.get_table_mapping_by_id(mapping_id)
    if not tm:
        raise HTTPException(404, "Tabellen-Mapping nicht gefunden")

    # Delete existing field mappings
    await db.execute(
        delete(EtlFieldMapping).where(
            EtlFieldMapping.table_mapping_id == mapping_id
        )
    )

    # Create new field mappings
    new_mappings = []
    for item in payload.field_mappings:
        fm = EtlFieldMapping(
            table_mapping_id=mapping_id,
            source_field=item.source_field,
            target_field=item.target_field,
            transform=item.transform,
            is_required=item.is_required,
            default_value=item.default_value,
            update_rule=item.update_rule,
        )
        db.add(fm)
        new_mappings.append(fm)

    # Save drawflow layout state
    if payload.drawflow_layout is not None:
        tm.drawflow_layout = json.dumps(payload.drawflow_layout)
    await db.flush()

    await db.commit()

    # Refresh to get generated IDs
    for fm in new_mappings:
        await db.refresh(fm)

    return BulkFieldMappingResponse(
        table_mapping_id=mapping_id,
        field_mappings_count=len(new_mappings),
        field_mappings=[
            EtlFieldMappingResponse.model_validate(fm) for fm in new_mappings
        ],
    )


# ============ Schema Discovery ============

@router.get("/schema/tables")
async def list_etl_tables(
    admin: ApiPartner = Depends(require_superadmin),
):
    """
    Liste aller für ETL verfügbaren Zieltabellen (nur Superadmin).

    Gibt nur Tabellen zurück, die in der Whitelist stehen.
    """
    return {"tables": sorted(ALLOWED_ETL_TABLES)}


@router.get("/schema/{table_name}", response_model=TableSchemaResponse)
async def get_table_schema(
    table_name: str,
    admin: ApiPartner = Depends(require_superadmin),
):
    """
    Spalten-Metadaten einer Zieltabelle abrufen (nur Superadmin).

    Verwendet SQLAlchemy Base.metadata für in-memory Schema-Lookup.
    """
    if table_name not in ALLOWED_ETL_TABLES:
        raise HTTPException(400, f"Tabelle '{table_name}' ist nicht für ETL verfügbar.")

    table = Base.metadata.tables.get(table_name)
    if table is None:
        raise HTTPException(404, f"Tabelle '{table_name}' nicht in Metadata gefunden.")

    columns = [
        TableColumnInfo(
            name=col.name,
            type=str(col.type),
            nullable=col.nullable if col.nullable is not None else True,
            is_pk=col.primary_key,
        )
        for col in table.columns
    ]
    return TableSchemaResponse(table_name=table_name, columns=columns)


# ============ Utility Endpoints ============

@router.get("/transforms", response_model=list[str])
async def list_transforms(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Liste aller verfügbaren Transformationen (nur Superadmin).

    Transformationen können im `transform`-Feld eines Feld-Mappings verwendet werden.
    """
    service = EtlService(db)
    return service.get_available_transforms()
