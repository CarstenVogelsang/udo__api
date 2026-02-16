"""
API Routes for Marke (Brand) CRUD operations.

Brands belong to a Hersteller (ComUnternehmen) and serve as
FK targets for ProdArtikel.marke_id and fk_lookup transforms.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.models.com import ComMarke, ComUnternehmen
from app.schemas.com import (
    ComMarkeRead,
    ComMarkeCreate,
    ComMarkeUpdate,
)

router = APIRouter(prefix="/marken", tags=["Marken"])


@router.get("")
async def list_marken(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    hersteller_id: str | None = Query(None, description="Filter nach Hersteller-UUID"),
    suche: str | None = Query(None, min_length=1, description="Suche im Markennamen"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Liste aller Marken mit optionalem Filter (nur Superadmin)."""
    query = select(ComMarke)
    count_query = select(func.count(ComMarke.id))

    if hersteller_id:
        query = query.where(ComMarke.hersteller_id == hersteller_id)
        count_query = count_query.where(ComMarke.hersteller_id == hersteller_id)
    if suche:
        query = query.where(ComMarke.name.ilike(f"%{suche}%"))
        count_query = count_query.where(ComMarke.name.ilike(f"%{suche}%"))

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(query.order_by(ComMarke.name).offset(skip).limit(limit))
    items = result.scalars().all()

    return {"items": [ComMarkeRead.model_validate(m) for m in items], "total": total}


@router.get("/{marke_id}", response_model=ComMarkeRead)
async def get_marke(
    marke_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Einzelne Marke abrufen (nur Superadmin)."""
    result = await db.execute(select(ComMarke).where(ComMarke.id == marke_id))
    marke = result.scalar_one_or_none()
    if not marke:
        raise HTTPException(status_code=404, detail="Marke nicht gefunden")
    return marke


@router.post("", response_model=ComMarkeRead, status_code=status.HTTP_201_CREATED)
async def create_marke(
    data: ComMarkeCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Neue Marke erstellen (nur Superadmin).

    **Pflichtfelder:** hersteller_id, name
    **Constraint:** (hersteller_id, name) muss eindeutig sein.
    """
    # Verify hersteller exists
    hersteller = await db.execute(
        select(ComUnternehmen).where(ComUnternehmen.id == data.hersteller_id)
    )
    if not hersteller.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Hersteller nicht gefunden")

    # Check uniqueness
    existing = await db.execute(
        select(ComMarke).where(
            ComMarke.hersteller_id == data.hersteller_id,
            ComMarke.name == data.name,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Marke '{data.name}' existiert bereits für diesen Hersteller",
        )

    marke = ComMarke(**data.model_dump())
    db.add(marke)
    await db.commit()
    await db.refresh(marke)
    return marke


@router.patch("/{marke_id}", response_model=ComMarkeRead)
async def update_marke(
    marke_id: str,
    data: ComMarkeUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Marke aktualisieren (nur Superadmin, partial update)."""
    result = await db.execute(select(ComMarke).where(ComMarke.id == marke_id))
    marke = result.scalar_one_or_none()
    if not marke:
        raise HTTPException(status_code=404, detail="Marke nicht gefunden")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    for key, value in update_data.items():
        setattr(marke, key, value)

    await db.commit()
    await db.refresh(marke)
    return marke


@router.delete("/{marke_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_marke(
    marke_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Marke löschen (nur Superadmin). Kaskadiert zu Serien."""
    result = await db.execute(select(ComMarke).where(ComMarke.id == marke_id))
    marke = result.scalar_one_or_none()
    if not marke:
        raise HTTPException(status_code=404, detail="Marke nicht gefunden")

    await db.delete(marke)
    await db.commit()
