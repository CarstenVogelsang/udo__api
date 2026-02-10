"""
API Routes for Excel Import.

Provides endpoints to upload Excel files and execute imports
using saved ETL configuration (EtlSource with connection_type="excel").
All endpoints are Superadmin only.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy import select, update, delete, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.models.com import ComUnternehmen, ComKontakt
from app.models.etl import EtlSource, EtlTableMapping, EtlImportLog, EtlImportRecord
from app.services.excel_import import ExcelImportService
from app.schemas.etl import (
    ExcelImportResult,
    ExcelSourcePreview,
    EtlFieldMappingResponse,
    EtlImportLogWithMapping,
    EtlImportLogList,
    EtlImportRecordResponse,
    EtlImportRecordList,
    EtlImportRollbackResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/etl/excel", tags=["Excel Import"])


@router.post("/upload/{source_name}", response_model=ExcelImportResult)
async def upload_and_import(
    source_name: str,
    file: UploadFile = File(...),
    dry_run: bool = Query(False, description="Testlauf ohne Schreiben"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload Excel file and execute import using saved EtlSource configuration.

    - source_name: Name der EtlSource (z.B. "ev_smartmail")
    - file: Excel-Datei (.xlsx)
    - dry_run: Wenn true, wird nur gezählt, nicht geschrieben
    """
    if not file.filename or not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Nur Excel-Dateien (.xlsx) werden unterstützt.")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50 MB limit
        raise HTTPException(400, "Datei ist zu groß (max. 50 MB).")

    service = ExcelImportService(db)
    try:
        result = await service.run_import(source_name, content, dry_run=dry_run)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.exception(f"Excel import failed: {e}")
        raise HTTPException(500, f"Import fehlgeschlagen: {str(e)}")

    return ExcelImportResult(**result)


@router.get("/preview/{source_name}", response_model=ExcelSourcePreview)
async def preview_mappings(
    source_name: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get the configured column mappings for an Excel import source."""
    result = await db.execute(
        select(EtlSource)
        .where(EtlSource.name == source_name)
        .where(EtlSource.connection_type == "excel")
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(404, f"Excel-Quelle '{source_name}' nicht gefunden.")

    # Load table mappings with field mappings
    result = await db.execute(
        select(EtlTableMapping)
        .where(EtlTableMapping.source_id == source.id)
        .where(EtlTableMapping.is_active.is_(True))
    )
    mappings = result.scalars().all()

    u_mappings = []
    k_mappings = []
    for m in mappings:
        fields = [EtlFieldMappingResponse.model_validate(f) for f in m.field_mappings]
        if m.target_table == "com_unternehmen":
            u_mappings = fields
        elif m.target_table == "com_kontakt":
            k_mappings = fields

    return ExcelSourcePreview(
        source_name=source.name,
        description=source.description,
        unternehmen_mappings=u_mappings,
        kontakt_mappings=k_mappings,
    )


@router.get("/sources")
async def list_excel_sources(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List all Excel import sources."""
    result = await db.execute(
        select(EtlSource)
        .where(EtlSource.connection_type == "excel")
        .order_by(EtlSource.name)
    )
    sources = result.scalars().all()
    return {
        "items": [
            {
                "name": s.name,
                "description": s.description,
                "is_active": s.is_active,
                "erstellt_am": s.erstellt_am,
            }
            for s in sources
        ],
        "total": len(sources),
    }


@router.get("/logs", response_model=EtlImportLogList)
async def list_import_logs(
    batch_id: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List Excel import logs, optionally filtered by batch_id."""
    query = (
        select(EtlImportLog)
        .join(EtlTableMapping)
        .join(EtlSource)
        .where(EtlSource.connection_type == "excel")
        .options(selectinload(EtlImportLog.table_mapping))
        .order_by(EtlImportLog.started_at.desc())
    )
    if batch_id:
        query = query.where(EtlImportLog.batch_id == batch_id)

    # Count
    from sqlalchemy import func
    count_query = (
        select(func.count(EtlImportLog.id))
        .join(EtlTableMapping)
        .join(EtlSource)
        .where(EtlSource.connection_type == "excel")
    )
    if batch_id:
        count_query = count_query.where(EtlImportLog.batch_id == batch_id)
    total = (await db.execute(count_query)).scalar() or 0

    result = await db.execute(query.offset(skip).limit(limit))
    logs = result.scalars().all()

    return EtlImportLogList(
        items=[EtlImportLogWithMapping.model_validate(log) for log in logs],
        total=total,
    )


# ============ Import Record Tracking ============

@router.get("/imports/{batch_id}/records", response_model=EtlImportRecordList)
async def list_import_records(
    batch_id: str,
    entity_type: str | None = Query(None, description="Filter: unternehmen, kontakt, junction:*"),
    action: str | None = Query(None, description="Filter: created, updated"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List all records created/updated by a specific import batch."""
    query = (
        select(EtlImportRecord)
        .where(EtlImportRecord.batch_id == batch_id)
        .order_by(EtlImportRecord.erstellt_am)
    )
    count_query = (
        select(func.count(EtlImportRecord.id))
        .where(EtlImportRecord.batch_id == batch_id)
    )

    if entity_type:
        query = query.where(EtlImportRecord.entity_type == entity_type)
        count_query = count_query.where(EtlImportRecord.entity_type == entity_type)
    if action:
        query = query.where(EtlImportRecord.action == action)
        count_query = count_query.where(EtlImportRecord.action == action)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset(skip).limit(limit))
    records = result.scalars().all()

    return EtlImportRecordList(
        items=[EtlImportRecordResponse.model_validate(r) for r in records],
        total=total,
        batch_id=batch_id,
    )


@router.post("/imports/{batch_id}/rollback", response_model=EtlImportRollbackResult)
async def rollback_import(
    batch_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft-delete all records that were CREATED by this import batch.

    Sets geloescht_am on Unternehmen and Kontakt records.
    Deletes junction table entries (no soft-delete on junction tables).
    Updated records are not rolled back.
    """
    result = await db.execute(
        select(EtlImportRecord)
        .where(EtlImportRecord.batch_id == batch_id)
        .where(EtlImportRecord.action == "created")
    )
    records = result.scalars().all()

    if not records:
        raise HTTPException(404, "Keine Import-Records für diesen Batch gefunden.")

    now = datetime.utcnow()
    rolled_back = 0
    skipped = 0
    details = []

    for rec in records:
        try:
            if rec.entity_type == "unternehmen":
                await db.execute(
                    update(ComUnternehmen)
                    .where(ComUnternehmen.id == rec.entity_id)
                    .where(ComUnternehmen.geloescht_am.is_(None))
                    .values(geloescht_am=now)
                )
                rolled_back += 1
            elif rec.entity_type == "kontakt":
                await db.execute(
                    update(ComKontakt)
                    .where(ComKontakt.id == rec.entity_id)
                    .where(ComKontakt.geloescht_am.is_(None))
                    .values(geloescht_am=now)
                )
                rolled_back += 1
            elif rec.entity_type.startswith("junction:"):
                table_name = rec.entity_type.split(":", 1)[1]
                await db.execute(
                    text(f"DELETE FROM {table_name} WHERE id = :id"),
                    {"id": str(rec.entity_id)},
                )
                rolled_back += 1
            else:
                skipped += 1
                details.append(f"Unbekannter Typ: {rec.entity_type}")
        except Exception as e:
            skipped += 1
            details.append(f"Fehler bei {rec.entity_type}:{rec.entity_id}: {str(e)}")

    await db.commit()

    return EtlImportRollbackResult(
        batch_id=batch_id,
        rolled_back=rolled_back,
        skipped=skipped,
        details=details,
    )
