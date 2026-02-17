"""Provider abstraction for external business data sources.

Defines the base interface for recherche providers and a registry
that maps quality tiers to provider combinations.
"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.models.recherche import RecherchQualitaetsStufe

logger = logging.getLogger(__name__)


@dataclass
class RohErgebnisData:
    """Normalized result from an external provider.

    This is the common data format that all providers must produce.
    The worker stores these in the rch_roh_ergebnis table.
    """
    name: str
    quelle: str                          # Provider name ("google_places", "dataforseo")
    externe_id: str | None = None        # place_id, listing_id, etc.
    adresse: str | None = None
    plz: str | None = None
    ort: str | None = None
    telefon: str | None = None
    website: str | None = None
    email: str | None = None
    kategorie: str | None = None
    lat: float | None = None
    lng: float | None = None
    rohdaten: dict | None = field(default_factory=dict)  # Full raw response


@dataclass
class SuchErgebnis:
    """Container for search results including actual API costs.

    Returned by provider.suchen(). Separates results from cost tracking.
    """
    ergebnisse: list[RohErgebnisData]
    api_kosten_usd: float = 0.0  # Actual cost reported by the API (in USD)


class RecherchProviderBase(ABC):
    """Abstract base class for external data providers.

    Each provider must implement the `suchen` method to query
    an external API and return normalized results.
    """
    name: str = "base"

    @abstractmethod
    async def suchen(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        suchbegriff: str,
        kategorie: str | None = None,
        max_ergebnisse: int = 60,
    ) -> SuchErgebnis:
        """Execute a search and return normalized results with API costs.

        Args:
            lat: Center latitude.
            lng: Center longitude.
            radius_m: Search radius in meters.
            suchbegriff: Search term (e.g., "Restaurant").
            kategorie: Optional category filter.
            max_ergebnisse: Maximum results to return.

        Returns:
            SuchErgebnis with results and actual API cost in USD.
        """

    @abstractmethod
    def get_kosten_pro_request(self) -> float:
        """Return external API cost per request (EUR).

        Used for internal cost tracking, not customer billing.
        """

    async def ist_konfiguriert(self) -> bool:
        """Check if this provider has valid credentials configured.

        Override in subclasses that need API keys.
        """
        return True


# ---- Quality Tier → Provider Mapping ----

# Maps each quality tier to the provider names it should use.
STUFE_PROVIDER_MAPPING: dict[str, list[str]] = {
    RecherchQualitaetsStufe.STANDARD.value: ["dataforseo"],
    RecherchQualitaetsStufe.PREMIUM.value: ["google_places"],
    RecherchQualitaetsStufe.KOMPLETT.value: ["google_places", "dataforseo"],
}


class ProviderRegistry:
    """Registry that maps quality tiers to provider instances.

    Usage:
        registry = ProviderRegistry()
        registry.register(GooglePlacesProvider(settings_service))
        registry.register(DataForSeoProvider(settings_service))

        providers = registry.get_providers("premium")
        for provider in providers:
            results = await provider.suchen(...)
    """

    def __init__(self):
        self._providers: dict[str, RecherchProviderBase] = {}

    def register(self, provider: RecherchProviderBase) -> None:
        """Register a provider instance by its name."""
        self._providers[provider.name] = provider
        logger.info(f"Registered recherche provider: {provider.name}")

    def get_providers(
        self, stufe: str,
    ) -> list[RecherchProviderBase]:
        """Get provider instances for a quality tier.

        Args:
            stufe: Quality tier value ("standard", "premium", "komplett").

        Returns:
            List of provider instances for this tier.

        Raises:
            ValueError: If tier is unknown or required providers not registered.
        """
        provider_names = STUFE_PROVIDER_MAPPING.get(stufe)
        if provider_names is None:
            raise ValueError(f"Unbekannte Qualitätsstufe: {stufe}")

        providers = []
        for name in provider_names:
            provider = self._providers.get(name)
            if provider:
                providers.append(provider)
            else:
                logger.warning(
                    f"Provider '{name}' not registered "
                    f"(required for tier '{stufe}')"
                )

        if not providers:
            raise ValueError(
                f"Keine Provider für Stufe '{stufe}' verfügbar. "
                f"Benötigt: {provider_names}"
            )

        return providers

    @property
    def available_providers(self) -> list[str]:
        """List all registered provider names."""
        return list(self._providers.keys())
