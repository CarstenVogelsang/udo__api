"""
API Routes for Hersteller-Recherche data (Profiltexte, Medien, Quellen, Vertriebsstruktur).

Also provides read-only endpoints for reference tables (Rechtsformen, Medienlizenzen).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.models.base import BasRechtsform, BasMedienLizenz
from app.models.com import (
    ComUnternehmen,
    ComMarke,
    ComSerie,
    ComProfiltext,
    ComMedien,
    ComQuelle,
    ComVertriebsstruktur,
)
from app.schemas.com import (
    BasRechtsformRead,
    BasMedienLizenzRead,
    ComProfiltextRead,
    ComProfiltextCreate,
    ComProfiltextUpdate,
    ComMedienRead,
    ComMedienCreate,
    ComMedienUpdate,
    ComQuelleRead,
    ComQuelleCreate,
    ComVertriebsstrukturRead,
    ComVertriebsstrukturCreate,
    ComVertriebsstrukturUpdate,
    ComSerieRead,
)

router = APIRouter(tags=["Hersteller-Recherche"])


# ============ Referenzdaten (Read-Only) ============


@router.get("/rechtsformen", response_model=list[BasRechtsformRead], tags=["Referenzdaten"])
async def list_rechtsformen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Rechtsformen auflisten (für Recherche-KI Lookups)."""
    result = await db.execute(
        select(BasRechtsform)
        .where(BasRechtsform.ist_aktiv == True)  # noqa: E712
        .order_by(BasRechtsform.land_code, BasRechtsform.name)
    )
    return result.scalars().all()


@router.get("/medien-lizenzen", response_model=list[BasMedienLizenzRead], tags=["Referenzdaten"])
async def list_medien_lizenzen(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Alle Medienlizenzen auflisten (für Recherche-KI Lookups)."""
    result = await db.execute(
        select(BasMedienLizenz)
        .where(BasMedienLizenz.ist_aktiv == True)  # noqa: E712
        .order_by(BasMedienLizenz.kategorie, BasMedienLizenz.name)
    )
    return result.scalars().all()


# ============ Helper: Entity existence checks ============


async def _get_unternehmen_or_404(db: AsyncSession, unternehmen_id: str) -> ComUnternehmen:
    result = await db.execute(
        select(ComUnternehmen).where(ComUnternehmen.id == unternehmen_id)
    )
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Unternehmen nicht gefunden")
    return obj


async def _get_marke_or_404(db: AsyncSession, marke_id: str) -> ComMarke:
    result = await db.execute(select(ComMarke).where(ComMarke.id == marke_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Marke nicht gefunden")
    return obj


async def _get_serie_or_404(db: AsyncSession, serie_id: str) -> ComSerie:
    result = await db.execute(select(ComSerie).where(ComSerie.id == serie_id))
    obj = result.scalar_one_or_none()
    if not obj:
        raise HTTPException(status_code=404, detail="Serie nicht gefunden")
    return obj


# ============ Profiltexte ============


@router.post(
    "/unternehmen/{unternehmen_id}/profiltexte",
    response_model=ComProfiltextRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_unternehmen_profiltext(
    unternehmen_id: str,
    data: ComProfiltextCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Profiltext für Unternehmen erstellen (Upsert: typ+sprache)."""
    await _get_unternehmen_or_404(db, unternehmen_id)

    # Upsert: check if profiltext with same typ+sprache exists
    result = await db.execute(
        select(ComProfiltext).where(
            ComProfiltext.unternehmen_id == unternehmen_id,
            ComProfiltext.typ == data.typ,
            ComProfiltext.sprache == data.sprache,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.text = data.text
        existing.quelle = data.quelle
        await db.commit()
        await db.refresh(existing)
        return existing

    profiltext = ComProfiltext(unternehmen_id=unternehmen_id, **data.model_dump())
    db.add(profiltext)
    await db.commit()
    await db.refresh(profiltext)
    return profiltext


@router.post(
    "/marken/{marke_id}/profiltexte",
    response_model=ComProfiltextRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_marke_profiltext(
    marke_id: str,
    data: ComProfiltextCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Profiltext für Marke erstellen (Upsert: typ+sprache)."""
    await _get_marke_or_404(db, marke_id)

    result = await db.execute(
        select(ComProfiltext).where(
            ComProfiltext.marke_id == marke_id,
            ComProfiltext.typ == data.typ,
            ComProfiltext.sprache == data.sprache,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.text = data.text
        existing.quelle = data.quelle
        await db.commit()
        await db.refresh(existing)
        return existing

    profiltext = ComProfiltext(marke_id=marke_id, **data.model_dump())
    db.add(profiltext)
    await db.commit()
    await db.refresh(profiltext)
    return profiltext


@router.post(
    "/serien/{serie_id}/profiltexte",
    response_model=ComProfiltextRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_serie_profiltext(
    serie_id: str,
    data: ComProfiltextCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Profiltext für Serie erstellen (Upsert: typ+sprache)."""
    await _get_serie_or_404(db, serie_id)

    result = await db.execute(
        select(ComProfiltext).where(
            ComProfiltext.serie_id == serie_id,
            ComProfiltext.typ == data.typ,
            ComProfiltext.sprache == data.sprache,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.text = data.text
        existing.quelle = data.quelle
        await db.commit()
        await db.refresh(existing)
        return existing

    profiltext = ComProfiltext(serie_id=serie_id, **data.model_dump())
    db.add(profiltext)
    await db.commit()
    await db.refresh(profiltext)
    return profiltext


@router.patch("/profiltexte/{profiltext_id}", response_model=ComProfiltextRead)
async def update_profiltext(
    profiltext_id: str,
    data: ComProfiltextUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Profiltext aktualisieren (partial update)."""
    result = await db.execute(
        select(ComProfiltext).where(ComProfiltext.id == profiltext_id)
    )
    profiltext = result.scalar_one_or_none()
    if not profiltext:
        raise HTTPException(status_code=404, detail="Profiltext nicht gefunden")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(profiltext, key, value)

    await db.commit()
    await db.refresh(profiltext)
    return profiltext


@router.delete("/profiltexte/{profiltext_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profiltext(
    profiltext_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Profiltext löschen."""
    result = await db.execute(
        select(ComProfiltext).where(ComProfiltext.id == profiltext_id)
    )
    profiltext = result.scalar_one_or_none()
    if not profiltext:
        raise HTTPException(status_code=404, detail="Profiltext nicht gefunden")

    await db.delete(profiltext)
    await db.commit()


# ============ Medien ============


@router.post(
    "/unternehmen/{unternehmen_id}/medien",
    response_model=ComMedienRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_unternehmen_medien(
    unternehmen_id: str,
    data: ComMedienCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Medium (Logo/Bild) für Unternehmen hinzufügen."""
    await _get_unternehmen_or_404(db, unternehmen_id)

    medium = ComMedien(unternehmen_id=unternehmen_id, **data.model_dump())
    db.add(medium)
    await db.commit()
    await db.refresh(medium)
    return medium


@router.post(
    "/marken/{marke_id}/medien",
    response_model=ComMedienRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_marke_medien(
    marke_id: str,
    data: ComMedienCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Medium (Logo/Bild) für Marke hinzufügen."""
    await _get_marke_or_404(db, marke_id)

    medium = ComMedien(marke_id=marke_id, **data.model_dump())
    db.add(medium)
    await db.commit()
    await db.refresh(medium)
    return medium


@router.patch("/medien/{medien_id}", response_model=ComMedienRead)
async def update_medien(
    medien_id: str,
    data: ComMedienUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Medium aktualisieren (partial update)."""
    result = await db.execute(select(ComMedien).where(ComMedien.id == medien_id))
    medium = result.scalar_one_or_none()
    if not medium:
        raise HTTPException(status_code=404, detail="Medium nicht gefunden")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(medium, key, value)

    await db.commit()
    await db.refresh(medium)
    return medium


@router.delete("/medien/{medien_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medien(
    medien_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Medium löschen."""
    result = await db.execute(select(ComMedien).where(ComMedien.id == medien_id))
    medium = result.scalar_one_or_none()
    if not medium:
        raise HTTPException(status_code=404, detail="Medium nicht gefunden")

    await db.delete(medium)
    await db.commit()


# ============ Quellen ============


@router.get(
    "/unternehmen/{unternehmen_id}/quellen",
    response_model=list[ComQuelleRead],
)
async def list_quellen(
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Quellen eines Unternehmens auflisten."""
    await _get_unternehmen_or_404(db, unternehmen_id)

    result = await db.execute(
        select(ComQuelle)
        .where(ComQuelle.unternehmen_id == unternehmen_id)
        .order_by(ComQuelle.erstellt_am)
    )
    return result.scalars().all()


@router.post(
    "/unternehmen/{unternehmen_id}/quellen",
    response_model=ComQuelleRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_quelle(
    unternehmen_id: str,
    data: ComQuelleCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Quelle für Unternehmen hinzufügen (Upsert: URL)."""
    await _get_unternehmen_or_404(db, unternehmen_id)

    # Upsert by URL
    result = await db.execute(
        select(ComQuelle).where(
            ComQuelle.unternehmen_id == unternehmen_id,
            ComQuelle.url == data.url,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.beschreibung = data.beschreibung or existing.beschreibung
        existing.abrufdatum = data.abrufdatum or existing.abrufdatum
        existing.quelle_typ = data.quelle_typ
        await db.commit()
        await db.refresh(existing)
        return existing

    quelle = ComQuelle(unternehmen_id=unternehmen_id, **data.model_dump())
    db.add(quelle)
    await db.commit()
    await db.refresh(quelle)
    return quelle


@router.delete("/quellen/{quelle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quelle(
    quelle_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Quelle löschen."""
    result = await db.execute(select(ComQuelle).where(ComQuelle.id == quelle_id))
    quelle = result.scalar_one_or_none()
    if not quelle:
        raise HTTPException(status_code=404, detail="Quelle nicht gefunden")

    await db.delete(quelle)
    await db.commit()


# ============ Vertriebsstruktur ============


@router.get(
    "/unternehmen/{unternehmen_id}/vertriebsstruktur",
    response_model=list[ComVertriebsstrukturRead],
)
async def list_vertriebsstruktur(
    unternehmen_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Vertriebskanäle eines Herstellers auflisten."""
    await _get_unternehmen_or_404(db, unternehmen_id)

    result = await db.execute(
        select(ComVertriebsstruktur)
        .where(ComVertriebsstruktur.hersteller_id == unternehmen_id)
        .order_by(ComVertriebsstruktur.sortierung)
    )
    return result.scalars().all()


@router.post(
    "/unternehmen/{unternehmen_id}/vertriebsstruktur",
    response_model=ComVertriebsstrukturRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_vertriebsstruktur(
    unternehmen_id: str,
    data: ComVertriebsstrukturCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Vertriebskanal für Hersteller hinzufügen."""
    await _get_unternehmen_or_404(db, unternehmen_id)
    # Verify lieferant exists
    await _get_unternehmen_or_404(db, data.lieferant_id)

    # Check uniqueness (hersteller + lieferant + region)
    result = await db.execute(
        select(ComVertriebsstruktur).where(
            ComVertriebsstruktur.hersteller_id == unternehmen_id,
            ComVertriebsstruktur.lieferant_id == data.lieferant_id,
            ComVertriebsstruktur.region == data.region,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="Vertriebskanal für diese Kombination (Hersteller/Lieferant/Region) existiert bereits",
        )

    vertrieb = ComVertriebsstruktur(
        hersteller_id=unternehmen_id, **data.model_dump()
    )
    db.add(vertrieb)
    await db.commit()
    await db.refresh(vertrieb)
    return vertrieb


@router.patch("/vertriebsstruktur/{vertrieb_id}", response_model=ComVertriebsstrukturRead)
async def update_vertriebsstruktur(
    vertrieb_id: str,
    data: ComVertriebsstrukturUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Vertriebskanal aktualisieren (partial update)."""
    result = await db.execute(
        select(ComVertriebsstruktur).where(ComVertriebsstruktur.id == vertrieb_id)
    )
    vertrieb = result.scalar_one_or_none()
    if not vertrieb:
        raise HTTPException(status_code=404, detail="Vertriebskanal nicht gefunden")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(vertrieb, key, value)

    await db.commit()
    await db.refresh(vertrieb)
    return vertrieb


@router.delete("/vertriebsstruktur/{vertrieb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vertriebsstruktur(
    vertrieb_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Vertriebskanal löschen."""
    result = await db.execute(
        select(ComVertriebsstruktur).where(ComVertriebsstruktur.id == vertrieb_id)
    )
    vertrieb = result.scalar_one_or_none()
    if not vertrieb:
        raise HTTPException(status_code=404, detail="Vertriebskanal nicht gefunden")

    await db.delete(vertrieb)
    await db.commit()


# ============ Serien (unter Marke) ============


@router.get("/marken/{marke_id}/serien", response_model=list[ComSerieRead])
async def list_serien_for_marke(
    marke_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Serien einer Marke auflisten."""
    await _get_marke_or_404(db, marke_id)

    result = await db.execute(
        select(ComSerie)
        .where(ComSerie.marke_id == marke_id)
        .order_by(ComSerie.name)
    )
    return result.scalars().all()


@router.post(
    "/marken/{marke_id}/serien",
    response_model=ComSerieRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_serie_for_marke(
    marke_id: str,
    name: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Serie für Marke erstellen (Dedup: Name+Marke)."""
    await _get_marke_or_404(db, marke_id)

    # Check uniqueness
    result = await db.execute(
        select(ComSerie).where(
            ComSerie.marke_id == marke_id,
            ComSerie.name == name,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing  # Idempotent: return existing

    serie = ComSerie(marke_id=marke_id, name=name)
    db.add(serie)
    await db.commit()
    await db.refresh(serie)
    return serie
