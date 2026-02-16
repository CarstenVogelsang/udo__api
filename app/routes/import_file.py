"""
API Routes for Import File management.

Provides endpoints for uploading, listing, and managing import files
that are centrally stored and auto-matched to EtlSource projects.
All endpoints are Superadmin only.
"""
import logging

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.config import get_settings
from app.models.partner import ApiPartner
from app.models.etl import EtlImportFile
from app.services.import_file import ImportFileService
from app.schemas.etl import (
    EtlImportFileResponse,
    EtlImportFileList,
    EtlImportFileAssign,
    EtlImportFileRowsResponse,
    CompatibilityReport,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/etl/files", tags=["Import Files"])


@router.post("", response_model=EtlImportFileResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Upload an Excel file for analysis and optional auto-assignment."""
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Nur Excel-Dateien (.xlsx, .xls) werden unterstützt.")

    content = await file.read()

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"Datei ist zu groß (max. {settings.max_upload_size_mb} MB).")

    service = ImportFileService(db)
    try:
        import_file = await service.upload_file(
            content=content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            uploaded_by=admin.name,
        )
        await db.commit()
        await db.refresh(import_file)
    except Exception as e:
        logger.exception(f"Upload failed: {e}")
        raise HTTPException(500, f"Upload fehlgeschlagen: {str(e)}")

    return EtlImportFileResponse.model_validate(import_file)


@router.get("", response_model=EtlImportFileList)
async def list_files(
    source_id: str | None = Query(None, description="Filter by source"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List import files with optional filtering."""
    query = select(EtlImportFile).order_by(EtlImportFile.erstellt_am.desc())
    count_query = select(func.count(EtlImportFile.id))

    if source_id:
        query = query.where(EtlImportFile.source_id == source_id)
        count_query = count_query.where(EtlImportFile.source_id == source_id)
    if status:
        query = query.where(EtlImportFile.status == status)
        count_query = count_query.where(EtlImportFile.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.offset(skip).limit(limit))
    files = result.scalars().all()

    return EtlImportFileList(
        items=[EtlImportFileResponse.model_validate(f) for f in files],
        total=total,
    )


@router.get("/{file_id}", response_model=EtlImportFileResponse)
async def get_file(
    file_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get details of a specific import file."""
    result = await db.execute(
        select(EtlImportFile).where(EtlImportFile.id == file_id)
    )
    import_file = result.scalar_one_or_none()
    if not import_file:
        raise HTTPException(404, "Import-Datei nicht gefunden.")

    return EtlImportFileResponse.model_validate(import_file)


@router.get("/{file_id}/rows", response_model=EtlImportFileRowsResponse)
async def get_file_rows(
    file_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(5000, ge=1, le=50000),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Read rows from a stored import file (paginated)."""
    result = await db.execute(
        select(EtlImportFile).where(EtlImportFile.id == file_id)
    )
    import_file = result.scalar_one_or_none()
    if not import_file:
        raise HTTPException(404, "Import-Datei nicht gefunden.")

    service = ImportFileService(db)
    try:
        headers, rows = service.get_file_rows(import_file, offset=offset, limit=limit)
    except FileNotFoundError:
        raise HTTPException(404, "Datei nicht auf dem Server gefunden.")
    except Exception as e:
        logger.exception(f"Row read failed: {e}")
        raise HTTPException(500, f"Fehler beim Lesen: {str(e)}")

    return EtlImportFileRowsResponse(
        file_id=str(import_file.id),
        headers=headers,
        rows=rows,
        total_rows=import_file.row_count or 0,
        offset=offset,
        limit=limit,
    )


@router.get("/{file_id}/compatibility/{source_id}", response_model=CompatibilityReport)
async def get_file_compatibility(
    file_id: str,
    source_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Detailed field-level compatibility between a file and a source."""
    result = await db.execute(
        select(EtlImportFile).where(EtlImportFile.id == file_id)
    )
    import_file = result.scalar_one_or_none()
    if not import_file:
        raise HTTPException(404, "Import-Datei nicht gefunden.")

    service = ImportFileService(db)
    try:
        report = await service.compute_compatibility(import_file, source_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        logger.exception(f"Compatibility check failed: {e}")
        raise HTTPException(500, f"Kompatibilitätsprüfung fehlgeschlagen: {str(e)}")

    return report


@router.put("/{file_id}/assign", response_model=EtlImportFileResponse)
async def assign_file(
    file_id: str,
    data: EtlImportFileAssign,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Manually assign an import file to an EtlSource."""
    result = await db.execute(
        select(EtlImportFile).where(EtlImportFile.id == file_id)
    )
    import_file = result.scalar_one_or_none()
    if not import_file:
        raise HTTPException(404, "Import-Datei nicht gefunden.")

    service = ImportFileService(db)
    try:
        import_file = await service.assign_to_source(import_file, data.source_id)
        await db.commit()
        await db.refresh(import_file)
    except Exception as e:
        logger.exception(f"Assignment failed: {e}")
        raise HTTPException(500, f"Zuordnung fehlgeschlagen: {str(e)}")

    return EtlImportFileResponse.model_validate(import_file)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Delete an import file from DB and disk."""
    result = await db.execute(
        select(EtlImportFile).where(EtlImportFile.id == file_id)
    )
    import_file = result.scalar_one_or_none()
    if not import_file:
        raise HTTPException(404, "Import-Datei nicht gefunden.")

    service = ImportFileService(db)
    try:
        await service.delete_file(import_file)
        await db.commit()
    except Exception as e:
        logger.exception(f"Delete failed: {e}")
        raise HTTPException(500, f"Löschen fehlgeschlagen: {str(e)}")
