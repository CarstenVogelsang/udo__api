"""Core service for Recherche-Auftrag lifecycle management.

Handles order creation, credit reservation, status transitions,
worker job pickup (FOR UPDATE SKIP LOCKED), and settlement.
"""
import logging
from datetime import datetime

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recherche import (
    RecherchAuftrag,
    RecherchAuftragStatus,
    RecherchQualitaetsStufe,
)
from app.services.billing import BillingService
from app.services.recherche_kosten import RecherchKostenService

logger = logging.getLogger(__name__)


class RecherchService:
    """Manages the full lifecycle of recherche orders."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.billing = BillingService(db)
        self.kosten = RecherchKostenService(db)

    # ---- Partner-facing operations ----

    async def schaetzung_erstellen(
        self,
        partner_id: str,
        geo_ort_id: str | None = None,
        geo_kreis_id: str | None = None,
        plz: str | None = None,
        wz_code: str | None = None,
        google_kategorie_gcid: str | None = None,
        branche_freitext: str | None = None,
        qualitaets_stufe: str = RecherchQualitaetsStufe.STANDARD.value,
    ) -> dict:
        """Create a cost estimation without committing to an order.

        Returns estimation dict (see RecherchKostenService.schaetzen).
        """
        return await self.kosten.schaetzen(
            partner_id=partner_id,
            geo_ort_id=geo_ort_id,
            geo_kreis_id=geo_kreis_id,
            plz=plz,
            wz_code=wz_code,
            google_kategorie_gcid=google_kategorie_gcid,
            branche_freitext=branche_freitext,
            qualitaets_stufe=qualitaets_stufe,
        )

    async def auftrag_erstellen(
        self,
        partner_id: str,
        geo_ort_id: str | None = None,
        geo_kreis_id: str | None = None,
        plz: str | None = None,
        wz_code: str | None = None,
        google_kategorie_gcid: str | None = None,
        branche_freitext: str | None = None,
        qualitaets_stufe: str = RecherchQualitaetsStufe.STANDARD.value,
    ) -> RecherchAuftrag:
        """Create a new recherche order and reserve credits.

        1. Estimate costs
        2. Reserve credits (estimation × 1.2 buffer)
        3. Create order with status BESTAETIGT

        Raises HTTPException 402 if insufficient credits.
        """
        # 1. Estimate
        schaetzung = await self.kosten.schaetzen(
            partner_id=partner_id,
            geo_ort_id=geo_ort_id,
            geo_kreis_id=geo_kreis_id,
            plz=plz,
            wz_code=wz_code,
            google_kategorie_gcid=google_kategorie_gcid,
            branche_freitext=branche_freitext,
            qualitaets_stufe=qualitaets_stufe,
        )

        # 2. Create order first (need ID for reservation reference)
        auftrag = RecherchAuftrag(
            partner_id=partner_id,
            geo_ort_id=geo_ort_id,
            geo_kreis_id=geo_kreis_id,
            plz=plz,
            wz_code=wz_code,
            google_kategorie_gcid=google_kategorie_gcid,
            branche_freitext=branche_freitext,
            qualitaets_stufe=qualitaets_stufe,
            status=RecherchAuftragStatus.BESTAETIGT.value,
            schaetzung_anzahl=schaetzung["geschaetzt_neu"],
            schaetzung_kosten_cents=schaetzung["geschaetzt_kosten_cents"],
            bestaetigt_am=datetime.utcnow(),
        )
        self.db.add(auftrag)
        await self.db.flush()  # Get auftrag.id

        # 3. Reserve credits with buffer
        reservierung_cents = self.kosten.reservierung_betrag(
            schaetzung["geschaetzt_kosten_cents"],
        )
        reservation_tx = await self.billing.reserve_credits(
            partner_id=partner_id,
            betrag_cents=reservierung_cents,
            beschreibung=(
                f"Recherche-Reservierung: ~{schaetzung['geschaetzt_neu']} Treffer "
                f"({qualitaets_stufe})"
            ),
            referenz_id=auftrag.id,
        )
        auftrag.reservierung_transaction_id = reservation_tx.id

        await self.db.flush()
        logger.info(
            f"Order created: {auftrag.id} partner={partner_id} "
            f"estimated={schaetzung['geschaetzt_neu']} "
            f"reserved={reservierung_cents}ct"
        )
        return auftrag

    async def auftrag_stornieren(
        self,
        auftrag_id: str,
        partner_id: str,
    ) -> RecherchAuftrag | None:
        """Cancel an order and refund reserved credits.

        Only possible while status is BESTAETIGT (not yet picked up by worker).

        Returns:
            Updated order, or None if not found / not cancellable.
        """
        result = await self.db.execute(
            select(RecherchAuftrag).where(
                RecherchAuftrag.id == auftrag_id,
                RecherchAuftrag.partner_id == partner_id,
            )
        )
        auftrag = result.scalar_one_or_none()
        if not auftrag:
            return None

        if auftrag.status != RecherchAuftragStatus.BESTAETIGT.value:
            return None  # Can only cancel before processing starts

        # Refund reserved credits
        if auftrag.reservierung_transaction_id:
            await self.billing.cancel_reservation(
                partner_id=partner_id,
                reservierung_transaction_id=auftrag.reservierung_transaction_id,
                beschreibung=f"Stornierung Recherche-Auftrag {auftrag.id[:8]}...",
                referenz_id=auftrag.id,
            )

        auftrag.status = RecherchAuftragStatus.STORNIERT.value
        await self.db.flush()

        logger.info(f"Order cancelled: {auftrag_id}")
        return auftrag

    async def get_auftraege(
        self,
        partner_id: str,
        status_filter: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """Get paginated orders for a partner.

        Returns:
            Dict with 'items' (list) and 'total' (int).
        """
        base = select(RecherchAuftrag).where(
            RecherchAuftrag.partner_id == partner_id,
        )
        if status_filter:
            base = base.where(RecherchAuftrag.status == status_filter)

        # Count
        count_q = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Items
        items_q = base.order_by(
            RecherchAuftrag.erstellt_am.desc(),
        ).offset(skip).limit(limit)
        result = await self.db.execute(items_q)
        items = result.scalars().all()

        return {"items": items, "total": total}

    async def get_auftrag(
        self,
        auftrag_id: str,
        partner_id: str | None = None,
    ) -> RecherchAuftrag | None:
        """Get a single order by ID, optionally filtered by partner."""
        query = select(RecherchAuftrag).where(
            RecherchAuftrag.id == auftrag_id,
        )
        if partner_id:
            query = query.where(RecherchAuftrag.partner_id == partner_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ---- Worker-facing operations ----

    async def naechsten_auftrag_holen(self) -> RecherchAuftrag | None:
        """Pick up the next order for processing.

        Uses SELECT ... FOR UPDATE SKIP LOCKED to ensure
        concurrent workers don't pick up the same order.

        Returns:
            Order to process, or None if queue is empty.
        """
        query = (
            select(RecherchAuftrag)
            .where(
                RecherchAuftrag.status == RecherchAuftragStatus.BESTAETIGT.value,
                RecherchAuftrag.versuche < RecherchAuftrag.max_versuche,
            )
            .order_by(RecherchAuftrag.erstellt_am.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
        )

        result = await self.db.execute(query)
        auftrag = result.scalar_one_or_none()

        if auftrag:
            auftrag.status = RecherchAuftragStatus.IN_BEARBEITUNG.value
            auftrag.worker_gestartet_am = datetime.utcnow()
            auftrag.versuche += 1
            await self.db.flush()
            logger.info(
                f"Worker picked up order: {auftrag.id} "
                f"attempt={auftrag.versuche}/{auftrag.max_versuche}"
            )

        return auftrag

    async def auftrag_abschliessen(
        self,
        auftrag_id: str,
        ergebnis_roh: int,
        ergebnis_neu: int,
        ergebnis_duplikat: int,
        ergebnis_aktualisiert: int,
        kosten_tatsaechlich_cents: int,
    ) -> RecherchAuftrag | None:
        """Mark an order as completed and settle credits.

        Called by the worker after successful processing.
        """
        result = await self.db.execute(
            select(RecherchAuftrag).where(RecherchAuftrag.id == auftrag_id)
        )
        auftrag = result.scalar_one_or_none()
        if not auftrag:
            return None

        # Update results
        auftrag.status = RecherchAuftragStatus.ABGESCHLOSSEN.value
        auftrag.ergebnis_anzahl_roh = ergebnis_roh
        auftrag.ergebnis_anzahl_neu = ergebnis_neu
        auftrag.ergebnis_anzahl_duplikat = ergebnis_duplikat
        auftrag.ergebnis_anzahl_aktualisiert = ergebnis_aktualisiert
        auftrag.kosten_tatsaechlich_cents = kosten_tatsaechlich_cents
        auftrag.worker_beendet_am = datetime.utcnow()
        auftrag.abgeschlossen_am = datetime.utcnow()

        # Settle credits (refund surplus)
        if auftrag.reservierung_transaction_id:
            settlement_tx = await self.billing.settle_reservation(
                partner_id=auftrag.partner_id,
                reservierung_transaction_id=auftrag.reservierung_transaction_id,
                tatsaechlich_cents=kosten_tatsaechlich_cents,
                beschreibung=(
                    f"Recherche abgeschlossen: {ergebnis_neu} neue Treffer "
                    f"({auftrag.qualitaets_stufe})"
                ),
                referenz_id=auftrag.id,
            )
            if settlement_tx:
                auftrag.abrechnung_transaction_id = settlement_tx.id

        await self.db.flush()
        logger.info(
            f"Order completed: {auftrag_id} "
            f"raw={ergebnis_roh} new={ergebnis_neu} "
            f"dup={ergebnis_duplikat} cost={kosten_tatsaechlich_cents}ct"
        )
        return auftrag

    async def auftrag_fehlgeschlagen(
        self,
        auftrag_id: str,
        fehler: str,
    ) -> RecherchAuftrag | None:
        """Mark an order as failed. May be retried if attempts remain.

        If max attempts reached, status stays FEHLGESCHLAGEN permanently.
        Otherwise, status reverts to BESTAETIGT for retry.
        """
        result = await self.db.execute(
            select(RecherchAuftrag).where(RecherchAuftrag.id == auftrag_id)
        )
        auftrag = result.scalar_one_or_none()
        if not auftrag:
            return None

        auftrag.fehler_meldung = fehler
        auftrag.worker_beendet_am = datetime.utcnow()

        if auftrag.versuche >= auftrag.max_versuche:
            # No more retries — mark as permanently failed
            auftrag.status = RecherchAuftragStatus.FEHLGESCHLAGEN.value
            logger.error(
                f"Order permanently failed: {auftrag_id} "
                f"after {auftrag.versuche} attempts: {fehler}"
            )

            # Cancel reservation (refund all credits)
            if auftrag.reservierung_transaction_id:
                await self.billing.cancel_reservation(
                    partner_id=auftrag.partner_id,
                    reservierung_transaction_id=auftrag.reservierung_transaction_id,
                    beschreibung=f"Recherche fehlgeschlagen: {fehler[:100]}",
                    referenz_id=auftrag.id,
                )
        else:
            # Retry: revert to BESTAETIGT
            auftrag.status = RecherchAuftragStatus.BESTAETIGT.value
            logger.warning(
                f"Order failed (will retry): {auftrag_id} "
                f"attempt={auftrag.versuche}/{auftrag.max_versuche}: {fehler}"
            )

        await self.db.flush()
        return auftrag
