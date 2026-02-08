"""
Business logic for API Usage Tracking.

Logs every partner API call with calculated costs.
Provides aggregation queries for dashboard and billing.
"""
from datetime import datetime, date, timedelta

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usage import ApiUsage, ApiUsageDaily
from app.models.partner import ApiPartner


class UsageService:
    """Service class for usage tracking operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_usage(
        self,
        partner_id: str,
        endpoint: str,
        methode: str,
        status_code: int,
        anzahl_ergebnisse: int,
        kosten: float,
        antwortzeit_ms: int | None = None,
        parameter: dict | None = None,
    ) -> ApiUsage:
        """Log a single API call."""
        usage = ApiUsage(
            partner_id=partner_id,
            endpoint=endpoint,
            methode=methode,
            status_code=status_code,
            anzahl_ergebnisse=anzahl_ergebnisse,
            kosten=kosten,
            antwortzeit_ms=antwortzeit_ms,
            parameter=parameter,
        )
        self.db.add(usage)
        await self.db.flush()
        return usage

    async def get_usage_meta(self, partner_id: str, kosten_abruf: float) -> dict:
        """
        Build _meta object for partner API responses.

        Returns dict with: kosten_abruf, kosten_heute, kosten_monat, abrufe_heute
        """
        heute = date.today()
        monat_start = heute.replace(day=1)

        # Today's stats
        heute_stats = await self.db.execute(
            select(
                func.count(ApiUsage.id).label("anzahl"),
                func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten"),
            ).where(
                and_(
                    ApiUsage.partner_id == partner_id,
                    func.date(ApiUsage.erstellt_am) == heute,
                )
            )
        )
        heute_row = heute_stats.one()

        # Month stats
        monat_stats = await self.db.execute(
            select(
                func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten"),
            ).where(
                and_(
                    ApiUsage.partner_id == partner_id,
                    func.date(ApiUsage.erstellt_am) >= monat_start,
                )
            )
        )
        monat_kosten = monat_stats.scalar() or 0.0

        # Billing info
        from app.services.billing import BillingService
        billing = BillingService(self.db)
        account = await billing.get_or_create_account(partner_id)

        return {
            "kosten_abruf": round(kosten_abruf, 6),
            "kosten_heute": round(float(heute_row.kosten) + kosten_abruf, 6),
            "kosten_monat": round(float(monat_kosten) + kosten_abruf, 6),
            "abrufe_heute": int(heute_row.anzahl) + 1,  # +1 for current request
            "guthaben_cents": account.guthaben_cents,
            "billing_typ": account.billing_typ,
        }

    async def get_partner_usage_aktuell(self, partner_id: str) -> dict:
        """
        Current usage stats for a partner (today + month).

        Returns dict compatible with UsageAktuell schema.
        """
        heute = date.today()
        monat_start = heute.replace(day=1)

        # Today's stats
        heute_stats = await self.db.execute(
            select(
                func.count(ApiUsage.id).label("anzahl"),
                func.coalesce(func.sum(ApiUsage.anzahl_ergebnisse), 0).label("ergebnisse"),
                func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten"),
            ).where(
                and_(
                    ApiUsage.partner_id == partner_id,
                    func.date(ApiUsage.erstellt_am) == heute,
                )
            )
        )
        heute_row = heute_stats.one()

        # Month stats
        monat_stats = await self.db.execute(
            select(
                func.count(ApiUsage.id).label("anzahl"),
                func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten"),
            ).where(
                and_(
                    ApiUsage.partner_id == partner_id,
                    func.date(ApiUsage.erstellt_am) >= monat_start,
                )
            )
        )
        monat_row = monat_stats.one()

        # Last request
        letzter = await self.db.execute(
            select(ApiUsage.erstellt_am)
            .where(ApiUsage.partner_id == partner_id)
            .order_by(ApiUsage.erstellt_am.desc())
            .limit(1)
        )
        letzter_abruf = letzter.scalar_one_or_none()

        return {
            "heute": {
                "datum": heute,
                "anzahl_abrufe": int(heute_row.anzahl),
                "anzahl_ergebnisse_gesamt": int(heute_row.ergebnisse),
                "kosten_gesamt": round(float(heute_row.kosten), 6),
            },
            "monat": {
                "monat": heute.strftime("%Y-%m"),
                "anzahl_abrufe": int(monat_row.anzahl),
                "kosten_gesamt": round(float(monat_row.kosten), 6),
            },
            "letzter_abruf": letzter_abruf,
        }

    async def get_partner_usage_historie(
        self,
        partner_id: str,
        skip: int = 0,
        limit: int = 30,
    ) -> dict:
        """
        Daily usage history for a partner (paginated).

        Returns dict compatible with UsageHistorieList schema.
        """
        base_filter = ApiUsage.partner_id == partner_id

        # Count distinct days
        count_query = select(
            func.count(func.distinct(func.date(ApiUsage.erstellt_am)))
        ).where(base_filter)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Daily aggregation
        daily_query = (
            select(
                func.date(ApiUsage.erstellt_am).label("datum"),
                func.count(ApiUsage.id).label("anzahl_abrufe"),
                func.coalesce(func.sum(ApiUsage.anzahl_ergebnisse), 0).label("anzahl_ergebnisse_gesamt"),
                func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten_gesamt"),
            )
            .where(base_filter)
            .group_by(func.date(ApiUsage.erstellt_am))
            .order_by(func.date(ApiUsage.erstellt_am).desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(daily_query)
        rows = result.all()

        items = [
            {
                "datum": row.datum,
                "anzahl_abrufe": int(row.anzahl_abrufe),
                "anzahl_ergebnisse_gesamt": int(row.anzahl_ergebnisse_gesamt),
                "kosten_gesamt": round(float(row.kosten_gesamt), 6),
            }
            for row in rows
        ]

        return {"items": items, "total": total}

    async def get_admin_usage_uebersicht(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> dict:
        """
        Usage overview of all partners (admin).

        Returns dict compatible with UsageAdminUebersichtList schema.
        """
        heute = date.today()
        monat_start = heute.replace(day=1)

        # Get all active partners
        partner_query = (
            select(ApiPartner)
            .where(ApiPartner.is_active == True)
            .order_by(ApiPartner.name)
            .offset(skip)
            .limit(limit)
        )
        partners = (await self.db.execute(partner_query)).scalars().all()

        total_query = select(func.count(ApiPartner.id)).where(ApiPartner.is_active == True)
        total = (await self.db.execute(total_query)).scalar() or 0

        items = []
        for p in partners:
            # Today's stats for this partner
            heute_stats = await self.db.execute(
                select(
                    func.count(ApiUsage.id).label("anzahl"),
                    func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten"),
                ).where(
                    and_(
                        ApiUsage.partner_id == p.id,
                        func.date(ApiUsage.erstellt_am) == heute,
                    )
                )
            )
            heute_row = heute_stats.one()

            # Month stats
            monat_stats = await self.db.execute(
                select(
                    func.count(ApiUsage.id).label("anzahl"),
                    func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten"),
                ).where(
                    and_(
                        ApiUsage.partner_id == p.id,
                        func.date(ApiUsage.erstellt_am) >= monat_start,
                    )
                )
            )
            monat_row = monat_stats.one()

            items.append({
                "partner_id": p.id,
                "partner_name": p.name,
                "abrufe_heute": int(heute_row.anzahl),
                "kosten_heute": round(float(heute_row.kosten), 6),
                "abrufe_monat": int(monat_row.anzahl),
                "kosten_monat": round(float(monat_row.kosten), 6),
            })

        return {"items": items, "total": total}

    async def get_admin_partner_usage(
        self,
        partner_id: str,
        von: date | None = None,
        bis: date | None = None,
    ) -> dict | None:
        """
        Detailed usage for a specific partner (admin).

        Returns dict compatible with UsageAdminPartnerDetail schema,
        or None if partner not found.
        """
        # Check partner exists
        partner = (await self.db.execute(
            select(ApiPartner).where(ApiPartner.id == partner_id)
        )).scalar_one_or_none()

        if not partner:
            return None

        # Default: last 30 days
        if not bis:
            bis = date.today()
        if not von:
            von = bis - timedelta(days=30)

        # Daily aggregation for date range
        daily_query = (
            select(
                func.date(ApiUsage.erstellt_am).label("datum"),
                func.count(ApiUsage.id).label("anzahl_abrufe"),
                func.coalesce(func.sum(ApiUsage.anzahl_ergebnisse), 0).label("anzahl_ergebnisse_gesamt"),
                func.coalesce(func.sum(ApiUsage.kosten), 0.0).label("kosten_gesamt"),
            )
            .where(
                and_(
                    ApiUsage.partner_id == partner_id,
                    func.date(ApiUsage.erstellt_am) >= von,
                    func.date(ApiUsage.erstellt_am) <= bis,
                )
            )
            .group_by(func.date(ApiUsage.erstellt_am))
            .order_by(func.date(ApiUsage.erstellt_am).desc())
        )
        result = await self.db.execute(daily_query)
        rows = result.all()

        tage = [
            {
                "datum": row.datum,
                "anzahl_abrufe": int(row.anzahl_abrufe),
                "anzahl_ergebnisse_gesamt": int(row.anzahl_ergebnisse_gesamt),
                "kosten_gesamt": round(float(row.kosten_gesamt), 6),
            }
            for row in rows
        ]

        gesamt_abrufe = sum(t["anzahl_abrufe"] for t in tage)
        gesamt_kosten = sum(t["kosten_gesamt"] for t in tage)

        return {
            "partner_id": partner.id,
            "partner_name": partner.name,
            "zeitraum_von": von,
            "zeitraum_bis": bis,
            "tage": tage,
            "gesamt_abrufe": gesamt_abrufe,
            "gesamt_kosten": round(gesamt_kosten, 6),
        }
