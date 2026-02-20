"""
Import service for Hersteller-Recherche JSON data.

Orchestrates the full import: validates, maps references, deduplicates,
and creates all entities in a single transaction.
"""
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BasRechtsform, BasMedienLizenz
from app.models.geo import GeoLand
from app.models.com import (
    ComUnternehmen,
    ComMarke,
    ComSerie,
    ComProfiltext,
    ComMedien,
    ComQuelle,
    ComVertriebsstruktur,
    ComKlassifikation,
    ComUnternehmenKlassifikation,
)
from app.schemas.hersteller_recherche import (
    HerstellerRechercheImport,
    ImportResult,
    ImportAktion,
    ImportMarkeResult,
    RechercheLogoInfo,
)


class HerstellerRechercheService:
    """Service for importing Hersteller-Recherche JSON data."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.warnungen: list[str] = []

    async def importiere(
        self,
        data: HerstellerRechercheImport,
        dry_run: bool = False,
    ) -> ImportResult:
        """Import a complete Hersteller-Recherche JSON."""
        self.warnungen = []
        counts = {
            "medien_angelegt": 0,
            "quellen_angelegt": 0,
            "profiltexte_angelegt": 0,
            "vertrieb_angelegt": 0,
        }

        h = data.hersteller

        # 1. Resolve references
        rechtsform_id = await self._resolve_rechtsform(h.rechtsform_code, h.rechtsform)
        herkunftsland_id = await self._resolve_herkunftsland(h.herkunftsland)

        # 2. Find or create Hersteller
        hersteller, h_aktion = await self._find_or_create_hersteller(
            name=h.name,
            name_kurz=h.name_kurz,
            website=h.website,
            gruendungsjahr=h.gruendungsjahr,
            gruender=h.gruender,
            rechtsform_id=rechtsform_id,
            herkunftsland_id=herkunftsland_id,
        )

        # 3. Profiltexte for Hersteller
        if h.profil_b2c:
            await self._upsert_profiltext(
                unternehmen_id=hersteller.id, typ="b2c", text=h.profil_b2c
            )
            counts["profiltexte_angelegt"] += 1
        if h.profil_b2b:
            await self._upsert_profiltext(
                unternehmen_id=hersteller.id, typ="b2b", text=h.profil_b2b
            )
            counts["profiltexte_angelegt"] += 1

        # 4. Hersteller-Logo
        if h.logo:
            await self._create_medien_from_logo(
                logo=h.logo,
                unternehmen_id=hersteller.id,
            )
            counts["medien_angelegt"] += 1

        # 5. GPSR: Create EU-Tochter/Bevollmächtigter
        if h.gpsr and h.gpsr.inverkehrbringer_eu:
            eu_rep = h.gpsr.inverkehrbringer_eu
            eu_unternehmen, _ = await self._find_or_create_hersteller(
                name=eu_rep.name,
                name_kurz=None,
                website=None,
                gruendungsjahr=None,
                gruender=None,
                rechtsform_id=None,
                herkunftsland_id=await self._resolve_herkunftsland(eu_rep.land),
            )
            # Set as default GPSR Bevollmächtigter
            if not hersteller.gpsr_default_bevollmaechtigter_id:
                hersteller.gpsr_default_bevollmaechtigter_id = eu_unternehmen.id

            # Assign Vertrieb: Tochtergesellschaft
            if h.vertrieb_dach and h.vertrieb_dach.tochtergesellschaft_de:
                tochter = h.vertrieb_dach.tochtergesellschaft_de
                if tochter.name == eu_rep.name:
                    # Same entity as EU rep
                    await self._upsert_vertriebsstruktur(
                        hersteller_id=hersteller.id,
                        lieferant_id=eu_unternehmen.id,
                        rolle="tochtergesellschaft",
                        region="DACH",
                        ist_empfohlen=True,
                        empfehlung_text=h.vertrieb_dach.empfehlung_bezugsweg,
                    )
                    counts["vertrieb_angelegt"] += 1

        # 6. Vertriebsstruktur (Hauptlieferant)
        if h.vertrieb_dach and h.vertrieb_dach.hauptlieferant_de:
            hl = h.vertrieb_dach.hauptlieferant_de
            hl_unternehmen, _ = await self._find_or_create_hersteller(
                name=hl.name, name_kurz=None, website=None,
                gruendungsjahr=None, gruender=None,
                rechtsform_id=None, herkunftsland_id=None,
            )
            await self._upsert_vertriebsstruktur(
                hersteller_id=hersteller.id,
                lieferant_id=hl_unternehmen.id,
                rolle=hl.typ or "hauptlieferant",
                region="DACH",
                ist_empfohlen=bool(
                    h.vertrieb_dach.empfehlung_bezugsweg
                    and hl.name in h.vertrieb_dach.empfehlung_bezugsweg
                ),
                empfehlung_text=h.vertrieb_dach.empfehlung_bezugsweg,
            )
            counts["vertrieb_angelegt"] += 1

        # 7. Marken + Serien
        marken_results = []
        for m in h.marken:
            marke, m_aktion = await self._find_or_create_marke(
                hersteller_id=hersteller.id, name=m.name
            )
            serien_count = 0

            # Marken-Profiltexte
            if m.profil_b2c:
                await self._upsert_profiltext(
                    marke_id=marke.id, typ="b2c", text=m.profil_b2c
                )
                counts["profiltexte_angelegt"] += 1
            if m.profil_b2b:
                await self._upsert_profiltext(
                    marke_id=marke.id, typ="b2b", text=m.profil_b2b
                )
                counts["profiltexte_angelegt"] += 1

            # Marken-Logo
            if m.logo:
                await self._create_medien_from_logo(
                    logo=m.logo, marke_id=marke.id
                )
                counts["medien_angelegt"] += 1

            # Serien
            for s in m.serien:
                serie, _ = await self._find_or_create_serie(
                    marke_id=marke.id, name=s.name
                )
                serien_count += 1

                if s.profil_b2c:
                    await self._upsert_profiltext(
                        serie_id=serie.id, typ="b2c", text=s.profil_b2c
                    )
                    counts["profiltexte_angelegt"] += 1
                if s.profil_b2b:
                    await self._upsert_profiltext(
                        serie_id=serie.id, typ="b2b", text=s.profil_b2b
                    )
                    counts["profiltexte_angelegt"] += 1

            marken_results.append(ImportMarkeResult(
                name=m.name, aktion=m_aktion, serien_angelegt=serien_count
            ))

        # 8. Quellen
        for q in data.quellen:
            await self._upsert_quelle(
                unternehmen_id=hersteller.id,
                url=q.url,
                beschreibung=q.beschreibung,
                abrufdatum=q.abrufdatum,
            )
            counts["quellen_angelegt"] += 1

        # 9. Klassifikationen: Hersteller + Lieferant
        await self._assign_klassifikation(hersteller.id, "hersteller")
        await self._assign_klassifikation(hersteller.id, "lieferant")

        # Commit or rollback
        if dry_run:
            await self.db.rollback()
        else:
            await self.db.commit()

        return ImportResult(
            status="dry_run" if dry_run else "success",
            hersteller=ImportAktion(id=str(hersteller.id), aktion=h_aktion),
            marken=marken_results,
            medien={"angelegt": counts["medien_angelegt"], "download_ausstehend": counts["medien_angelegt"]},
            quellen={"angelegt": counts["quellen_angelegt"]},
            profiltexte={"angelegt": counts["profiltexte_angelegt"]},
            vertriebsstruktur={"angelegt": counts["vertrieb_angelegt"]},
            warnungen=self.warnungen,
        )

    # ============ Private helpers ============

    async def _resolve_rechtsform(
        self, code: str | None, freitext: str | None
    ) -> str | None:
        if code:
            result = await self.db.execute(
                select(BasRechtsform).where(BasRechtsform.code == code)
            )
            rf = result.scalar_one_or_none()
            if rf:
                return rf.id
            self.warnungen.append(f"Rechtsform-Code '{code}' nicht gefunden")

        if freitext:
            self.warnungen.append(
                f"Rechtsform '{freitext}' konnte nicht automatisch gemappt werden"
            )
        return None

    async def _resolve_herkunftsland(self, code: str | None) -> str | None:
        if not code:
            return None
        result = await self.db.execute(
            select(GeoLand).where(GeoLand.code == code)
        )
        land = result.scalar_one_or_none()
        if land:
            return land.id
        self.warnungen.append(f"Herkunftsland '{code}' nicht in geo_land gefunden")
        return None

    async def _resolve_lizenz(
        self, code: str | None, freitext: str | None
    ) -> tuple[str | None, str | None]:
        """Returns (lizenz_id, lizenz_hinweis)."""
        if code:
            result = await self.db.execute(
                select(BasMedienLizenz).where(BasMedienLizenz.code == code)
            )
            lizenz = result.scalar_one_or_none()
            if lizenz:
                return lizenz.id, None

        # Try to match freitext to known codes
        if freitext:
            # Extract code-like part before parentheses
            code_part = freitext.split("(")[0].strip().lower().replace("-", "_").replace(" ", "_")
            result = await self.db.execute(
                select(BasMedienLizenz).where(BasMedienLizenz.code == code_part)
            )
            lizenz = result.scalar_one_or_none()
            if lizenz:
                return lizenz.id, None

            # Fallback: store as hint
            return None, freitext

        return None, None

    async def _find_or_create_hersteller(
        self,
        name: str,
        name_kurz: str | None,
        website: str | None,
        gruendungsjahr: int | None,
        gruender: str | None,
        rechtsform_id: str | None,
        herkunftsland_id: str | None,
    ) -> tuple[ComUnternehmen, str]:
        """Find existing or create new ComUnternehmen. Returns (obj, aktion)."""
        # Dedup: Try website first, then kurzname
        if website:
            result = await self.db.execute(
                select(ComUnternehmen).where(ComUnternehmen.website == website)
            )
            existing = result.scalar_one_or_none()
            if existing:
                # Fill in missing fields only
                changed = False
                if gruendungsjahr and not existing.gruendungsjahr:
                    existing.gruendungsjahr = gruendungsjahr
                    changed = True
                if gruender and not existing.gruender:
                    existing.gruender = gruender
                    changed = True
                if rechtsform_id and not existing.rechtsform_id:
                    existing.rechtsform_id = rechtsform_id
                    changed = True
                if herkunftsland_id and not existing.herkunftsland_id:
                    existing.herkunftsland_id = herkunftsland_id
                    changed = True
                return existing, "aktualisiert" if changed else "unveraendert"

        kurzname = name_kurz or name
        result = await self.db.execute(
            select(ComUnternehmen).where(ComUnternehmen.kurzname == kurzname)
        )
        existing = result.scalar_one_or_none()
        if existing:
            changed = False
            if website and not existing.website:
                existing.website = website
                changed = True
            if gruendungsjahr and not existing.gruendungsjahr:
                existing.gruendungsjahr = gruendungsjahr
                changed = True
            if gruender and not existing.gruender:
                existing.gruender = gruender
                changed = True
            if rechtsform_id and not existing.rechtsform_id:
                existing.rechtsform_id = rechtsform_id
                changed = True
            if herkunftsland_id and not existing.herkunftsland_id:
                existing.herkunftsland_id = herkunftsland_id
                changed = True
            return existing, "aktualisiert" if changed else "unveraendert"

        # Create new
        unternehmen = ComUnternehmen(
            kurzname=kurzname,
            firmierung=name if name != kurzname else None,
            website=website,
            gruendungsjahr=gruendungsjahr,
            gruender=gruender,
            rechtsform_id=rechtsform_id,
            herkunftsland_id=herkunftsland_id,
        )
        self.db.add(unternehmen)
        await self.db.flush()  # Get ID without committing
        return unternehmen, "angelegt"

    async def _find_or_create_marke(
        self, hersteller_id: str, name: str
    ) -> tuple[ComMarke, str]:
        result = await self.db.execute(
            select(ComMarke).where(
                ComMarke.hersteller_id == hersteller_id,
                ComMarke.name == name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing, "unveraendert"

        marke = ComMarke(hersteller_id=hersteller_id, name=name)
        self.db.add(marke)
        await self.db.flush()
        return marke, "angelegt"

    async def _find_or_create_serie(
        self, marke_id: str, name: str
    ) -> tuple[ComSerie, str]:
        result = await self.db.execute(
            select(ComSerie).where(
                ComSerie.marke_id == marke_id,
                ComSerie.name == name,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing, "unveraendert"

        serie = ComSerie(marke_id=marke_id, name=name)
        self.db.add(serie)
        await self.db.flush()
        return serie, "angelegt"

    async def _upsert_profiltext(
        self,
        typ: str,
        text: str,
        unternehmen_id: str | None = None,
        marke_id: str | None = None,
        serie_id: str | None = None,
    ) -> ComProfiltext:
        conditions = [ComProfiltext.typ == typ, ComProfiltext.sprache == "de"]
        if unternehmen_id:
            conditions.append(ComProfiltext.unternehmen_id == unternehmen_id)
        elif marke_id:
            conditions.append(ComProfiltext.marke_id == marke_id)
        elif serie_id:
            conditions.append(ComProfiltext.serie_id == serie_id)

        result = await self.db.execute(select(ComProfiltext).where(*conditions))
        existing = result.scalar_one_or_none()

        if existing:
            if not existing.text or existing.quelle == "recherche_ki":
                existing.text = text
                existing.quelle = "recherche_ki"
            return existing

        profiltext = ComProfiltext(
            unternehmen_id=unternehmen_id,
            marke_id=marke_id,
            serie_id=serie_id,
            typ=typ,
            sprache="de",
            text=text,
            quelle="recherche_ki",
        )
        self.db.add(profiltext)
        await self.db.flush()
        return profiltext

    async def _create_medien_from_logo(
        self,
        logo: RechercheLogoInfo,
        unternehmen_id: str | None = None,
        marke_id: str | None = None,
    ) -> ComMedien:
        lizenz_id, lizenz_hinweis = await self._resolve_lizenz(
            logo.lizenz_code, logo.lizenz
        )

        medium = ComMedien(
            unternehmen_id=unternehmen_id,
            marke_id=marke_id,
            medienart="LOGO",
            dateiname=logo.dateiname,
            dateiformat=logo.format,
            url_quelle=logo.quelle_url,
            ist_heruntergeladen=False,
            lizenz_id=lizenz_id,
            lizenz_hinweis=lizenz_hinweis,
        )
        self.db.add(medium)
        await self.db.flush()
        return medium

    async def _upsert_quelle(
        self,
        unternehmen_id: str,
        url: str,
        beschreibung: str | None,
        abrufdatum: date | None,
    ) -> ComQuelle:
        result = await self.db.execute(
            select(ComQuelle).where(
                ComQuelle.unternehmen_id == unternehmen_id,
                ComQuelle.url == url,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            if beschreibung:
                existing.beschreibung = beschreibung
            if abrufdatum:
                existing.abrufdatum = abrufdatum
            return existing

        quelle = ComQuelle(
            unternehmen_id=unternehmen_id,
            url=url,
            beschreibung=beschreibung,
            abrufdatum=abrufdatum,
            quelle_typ="recherche_ki",
        )
        self.db.add(quelle)
        await self.db.flush()
        return quelle

    async def _upsert_vertriebsstruktur(
        self,
        hersteller_id: str,
        lieferant_id: str,
        rolle: str,
        region: str | None,
        ist_empfohlen: bool = False,
        empfehlung_text: str | None = None,
    ) -> ComVertriebsstruktur:
        result = await self.db.execute(
            select(ComVertriebsstruktur).where(
                ComVertriebsstruktur.hersteller_id == hersteller_id,
                ComVertriebsstruktur.lieferant_id == lieferant_id,
                ComVertriebsstruktur.region == region,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        vertrieb = ComVertriebsstruktur(
            hersteller_id=hersteller_id,
            lieferant_id=lieferant_id,
            rolle=rolle,
            region=region,
            ist_empfohlen=ist_empfohlen,
            empfehlung_text=empfehlung_text,
        )
        self.db.add(vertrieb)
        await self.db.flush()
        return vertrieb

    async def _assign_klassifikation(
        self, unternehmen_id: str, slug: str
    ) -> None:
        # Find klassifikation by slug
        result = await self.db.execute(
            select(ComKlassifikation).where(ComKlassifikation.slug == slug)
        )
        klass = result.scalar_one_or_none()
        if not klass:
            self.warnungen.append(f"Klassifikation '{slug}' nicht gefunden")
            return

        # Check if already assigned
        result = await self.db.execute(
            select(ComUnternehmenKlassifikation).where(
                ComUnternehmenKlassifikation.unternehmen_id == unternehmen_id,
                ComUnternehmenKlassifikation.klassifikation_id == klass.id,
            )
        )
        if result.scalar_one_or_none():
            return

        zuordnung = ComUnternehmenKlassifikation(
            unternehmen_id=unternehmen_id,
            klassifikation_id=klass.id,
            quelle="recherche_ki",
        )
        self.db.add(zuordnung)
        await self.db.flush()
