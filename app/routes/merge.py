"""
API Routes for ETL Merge Configuration.

Provides CRUD for merge configs and join steps, plus
preview and execute endpoints to merge multiple source files.
"""
import json

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.models.etl import EtlMergeConfig, EtlMergeJoin, EtlImportFile, EtlSource
from app.schemas.merge import (
    EtlMergeConfigRead,
    EtlMergeConfigCreate,
    EtlMergeConfigUpdate,
    EtlMergeJoinRead,
    EtlMergeJoinCreate,
    EtlMergeJoinUpdate,
    MergePreviewResponse,
    MergeExecuteResponse,
)
from app.services.merge import MergeService

router = APIRouter(prefix="/etl/merge-configs", tags=["ETL Merge"])


# ============ MergeConfig CRUD ============


@router.get("")
async def list_merge_configs(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    source_id: str | None = Query(None, description="Filter nach Source-UUID"),
):
    """Liste aller Merge-Konfigurationen."""
    query = select(EtlMergeConfig)
    if source_id:
        query = query.where(EtlMergeConfig.source_id == source_id)
    result = await db.execute(query.order_by(EtlMergeConfig.erstellt_am.desc()))
    items = result.scalars().all()
    return {
        "items": [EtlMergeConfigRead.model_validate(c) for c in items],
        "total": len(items),
    }


@router.get("/{config_id}", response_model=EtlMergeConfigRead)
async def get_merge_config(
    config_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Merge-Config mit allen Join-Schritten laden."""
    result = await db.execute(
        select(EtlMergeConfig).where(EtlMergeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="MergeConfig nicht gefunden")
    return config


@router.post("", response_model=EtlMergeConfigRead, status_code=status.HTTP_201_CREATED)
async def create_merge_config(
    data: EtlMergeConfigCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Neue Merge-Config erstellen."""
    # Verify source exists
    source = await db.execute(
        select(EtlSource).where(EtlSource.id == data.source_id)
    )
    if not source.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="EtlSource nicht gefunden")

    # Check uniqueness (one config per source)
    existing = await db.execute(
        select(EtlMergeConfig).where(EtlMergeConfig.source_id == data.source_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Diese Source hat bereits eine Merge-Konfiguration",
        )

    config = EtlMergeConfig(
        source_id=data.source_id,
        name=data.name,
        beschreibung=data.beschreibung,
        primary_file_role=data.primary_file_role,
        output_renames=json.dumps(data.output_renames) if data.output_renames else None,
        output_drop_cols=json.dumps(data.output_drop_cols) if data.output_drop_cols else None,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config


@router.put("/{config_id}", response_model=EtlMergeConfigRead)
async def update_merge_config(
    config_id: str,
    data: EtlMergeConfigUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Merge-Config aktualisieren."""
    result = await db.execute(
        select(EtlMergeConfig).where(EtlMergeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="MergeConfig nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("output_renames", "output_drop_cols") and value is not None:
            value = json.dumps(value)
        setattr(config, key, value)

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_merge_config(
    config_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Merge-Config löschen (kaskadiert zu Join-Schritten)."""
    result = await db.execute(
        select(EtlMergeConfig).where(EtlMergeConfig.id == config_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="MergeConfig nicht gefunden")

    await db.delete(config)
    await db.commit()


# ============ Join Steps CRUD ============


@router.post("/{config_id}/joins", response_model=EtlMergeJoinRead, status_code=status.HTTP_201_CREATED)
async def create_join(
    config_id: str,
    data: EtlMergeJoinCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Join-Schritt hinzufügen."""
    # Verify config exists
    result = await db.execute(
        select(EtlMergeConfig).where(EtlMergeConfig.id == config_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="MergeConfig nicht gefunden")

    join = EtlMergeJoin(
        merge_config_id=config_id,
        file_role=data.file_role,
        join_type=data.join_type,
        join_col_left=data.join_col_left,
        join_col_right=data.join_col_right,
        columns_include=json.dumps(data.columns_include) if data.columns_include else None,
        column_renames=json.dumps(data.column_renames) if data.column_renames else None,
        deduplicate=data.deduplicate,
        sortierung=data.sortierung,
    )
    db.add(join)
    await db.commit()
    await db.refresh(join)
    return join


@router.put("/{config_id}/joins/{join_id}", response_model=EtlMergeJoinRead)
async def update_join(
    config_id: str,
    join_id: str,
    data: EtlMergeJoinUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Join-Schritt aktualisieren."""
    result = await db.execute(
        select(EtlMergeJoin).where(
            EtlMergeJoin.id == join_id,
            EtlMergeJoin.merge_config_id == config_id,
        )
    )
    join = result.scalar_one_or_none()
    if not join:
        raise HTTPException(status_code=404, detail="Join-Schritt nicht gefunden")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("columns_include", "column_renames") and value is not None:
            value = json.dumps(value)
        setattr(join, key, value)

    await db.commit()
    await db.refresh(join)
    return join


@router.delete("/{config_id}/joins/{join_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_join(
    config_id: str,
    join_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Join-Schritt entfernen."""
    result = await db.execute(
        select(EtlMergeJoin).where(
            EtlMergeJoin.id == join_id,
            EtlMergeJoin.merge_config_id == config_id,
        )
    )
    join = result.scalar_one_or_none()
    if not join:
        raise HTTPException(status_code=404, detail="Join-Schritt nicht gefunden")

    await db.delete(join)
    await db.commit()


# ============ Preview & Execute ============


@router.post("/{config_id}/preview", response_model=MergePreviewResponse)
async def preview_merge(
    config_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=100, description="Anzahl Vorschau-Zeilen"),
):
    """Merge-Vorschau (erste N Zeilen + Statistiken)."""
    service = MergeService(db)
    try:
        return await service.preview_merge(config_id, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{config_id}/execute", response_model=MergeExecuteResponse)
async def execute_merge(
    config_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Merge ausführen und neue Import-Datei erstellen."""
    service = MergeService(db)
    try:
        return await service.execute_merge(config_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ File Role Assignment ============


@router.put("/files/{file_id}/role")
async def assign_file_role(
    file_id: str,
    role: str = Query(..., description="Rolle der Datei (z.B. 'hauptdatei', 'haendlerpreise')"),
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Datei eine Rolle zuweisen (für Merge-Zuordnung)."""
    result = await db.execute(
        select(EtlImportFile).where(EtlImportFile.id == file_id)
    )
    import_file = result.scalar_one_or_none()
    if not import_file:
        raise HTTPException(status_code=404, detail="Import-Datei nicht gefunden")

    import_file.file_role = role
    await db.commit()
    await db.refresh(import_file)
    return {
        "id": str(import_file.id),
        "file_role": import_file.file_role,
        "original_filename": import_file.original_filename,
    }
