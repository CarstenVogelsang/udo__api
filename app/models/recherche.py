"""SQLAlchemy Models for Recherche-Auftrag (async data research workflow).

Partners can request business data that doesn't exist yet in the UDO database.
The system researches external APIs (Google Places, DataForSEO), deduplicates
results against existing data, and stores new companies in com_unternehmen.

Table prefix: rch_
"""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    JSON,
)
from sqlalchemy.orm import relationship

from app.models.geo import Base, UUID, generate_uuid


class RecherchAuftragStatus(str, PyEnum):
    """Status lifecycle of a research order."""
    BESTAETIGT = "bestaetigt"           # Credits reserved, waiting for worker
    IN_BEARBEITUNG = "in_bearbeitung"   # Worker is processing
    ABGESCHLOSSEN = "abgeschlossen"     # Completed successfully
    FEHLGESCHLAGEN = "fehlgeschlagen"   # Failed (may retry)
    STORNIERT = "storniert"             # Cancelled by partner


class RecherchQualitaetsStufe(str, PyEnum):
    """Quality tier — determines which providers are used.

    Customers choose a tier, not a specific provider.
    Internal mapping:
        STANDARD → DataForSEO (cheap, basic data)
        PREMIUM  → Google Places (rich data)
        KOMPLETT → Both sources (maximum coverage)
    """
    STANDARD = "standard"
    PREMIUM = "premium"
    KOMPLETT = "komplett"


class RecherchAuftrag(Base):
    """Research order for external business data acquisition.

    Lifecycle:
    1. Partner requests estimation (no order created)
    2. Partner creates order → credits reserved → status=BESTAETIGT
    3. Worker picks up → status=IN_BEARBEITUNG
    4. Worker finishes → status=ABGESCHLOSSEN, credits settled
    5. On failure → status=FEHLGESCHLAGEN, retries up to max_versuche
    """
    __tablename__ = "rch_auftrag"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    partner_id = Column(UUID, ForeignKey("api_partner.id"), nullable=False)

    # --- Geographic scope (at least one required) ---
    geo_ort_id = Column(UUID, ForeignKey("geo_ort.id"), nullable=True)
    geo_kreis_id = Column(UUID, ForeignKey("geo_kreis.id"), nullable=True)
    plz = Column(String(10), nullable=True)

    # --- Industry filter (at least one required) ---
    wz_code = Column(String(20), nullable=True)
    google_kategorie_gcid = Column(String(50), nullable=True)
    branche_freitext = Column(String(255), nullable=True)

    # --- Quality tier ---
    qualitaets_stufe = Column(
        String(20), nullable=False, default=RecherchQualitaetsStufe.STANDARD.value,
    )

    # --- Status ---
    status = Column(
        String(20), nullable=False, default=RecherchAuftragStatus.BESTAETIGT.value,
    )

    # --- Cost estimation ---
    schaetzung_anzahl = Column(Integer, nullable=True)        # Estimated new results
    schaetzung_kosten_cents = Column(Integer, nullable=True)   # Estimated cost

    # --- Actual results ---
    ergebnis_anzahl_roh = Column(Integer, default=0)           # Raw results from providers
    ergebnis_anzahl_neu = Column(Integer, default=0)           # New companies created
    ergebnis_anzahl_duplikat = Column(Integer, default=0)      # Duplicates found
    ergebnis_anzahl_aktualisiert = Column(Integer, default=0)  # Existing updated

    # --- Actual cost (charged to customer) ---
    kosten_tatsaechlich_cents = Column(Integer, nullable=True)

    # --- Purchase cost (actual API cost, in USD) ---
    einkaufskosten_usd = Column(Numeric(10, 4), nullable=True)

    # --- Credit reservation tracking ---
    reservierung_transaction_id = Column(UUID, nullable=True)  # ApiCreditTransaction.id
    abrechnung_transaction_id = Column(UUID, nullable=True)    # Final settlement tx

    # --- Worker state ---
    worker_gestartet_am = Column(DateTime, nullable=True)
    worker_beendet_am = Column(DateTime, nullable=True)
    fehler_meldung = Column(Text, nullable=True)
    versuche = Column(Integer, nullable=False, default=0)
    max_versuche = Column(Integer, nullable=False, default=3)

    # --- Timestamps ---
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    bestaetigt_am = Column(DateTime, nullable=True)
    abgeschlossen_am = Column(DateTime, nullable=True)

    # --- Relationships ---
    rohergebnisse = relationship(
        "RecherchRohErgebnis",
        back_populates="auftrag",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_rch_auftrag_partner", "partner_id"),
        Index("idx_rch_auftrag_status", "status"),
        Index("idx_rch_auftrag_erstellt", "erstellt_am"),
    )

    def __repr__(self):
        return (
            f"<RecherchAuftrag {self.id[:8]}... "
            f"status={self.status} stufe={self.qualitaets_stufe}>"
        )


class RecherchRohErgebnis(Base):
    """Raw result from an external provider before deduplication.

    Stores normalized data from Google Places, DataForSEO, etc.
    After deduplication, marked as duplicate or linked to a new ComUnternehmen.
    """
    __tablename__ = "rch_roh_ergebnis"

    id = Column(UUID, primary_key=True, default=generate_uuid)
    auftrag_id = Column(
        UUID, ForeignKey("rch_auftrag.id", ondelete="CASCADE"), nullable=False,
    )

    # --- Source ---
    quelle = Column(String(30), nullable=False)  # "google_places", "dataforseo"
    externe_id = Column(String(255), nullable=True)  # place_id, etc.

    # --- Normalized business data ---
    name = Column(String(255), nullable=False)
    adresse = Column(String(500), nullable=True)
    plz = Column(String(10), nullable=True)
    ort = Column(String(100), nullable=True)
    telefon = Column(String(50), nullable=True)
    website = Column(String(500), nullable=True)
    email = Column(String(255), nullable=True)
    kategorie = Column(String(255), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)

    # --- Full raw response (for debugging / re-processing) ---
    rohdaten = Column(JSON, nullable=True)

    # --- Deduplication result ---
    ist_duplikat = Column(Boolean, default=False)
    duplikat_von_id = Column(UUID, nullable=True)   # com_unternehmen.id if duplicate
    unternehmen_id = Column(UUID, nullable=True)     # com_unternehmen.id if newly created
    verarbeitet_am = Column(DateTime, nullable=True)

    # --- Timestamps ---
    erstellt_am = Column(DateTime, default=datetime.utcnow)

    # --- Relationships ---
    auftrag = relationship("RecherchAuftrag", back_populates="rohergebnisse")

    __table_args__ = (
        Index("idx_rch_roh_auftrag", "auftrag_id"),
        Index("idx_rch_roh_quelle", "quelle"),
        Index("idx_rch_roh_externe_id", "externe_id"),
    )

    def __repr__(self):
        status = "DUP" if self.ist_duplikat else ("NEW" if self.unternehmen_id else "RAW")
        return f"<RecherchRohErgebnis {self.name} [{status}] ({self.quelle})>"
