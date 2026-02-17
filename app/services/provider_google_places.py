"""Google Places API (New) provider for business data recherche.

Uses the Google Places API v1 (New) for Nearby Search to find
businesses in a geographic area.

API Docs: https://developers.google.com/maps/documentation/places/web-service/nearby-search
Pricing: ~$0.032 per Basic Nearby Search request (up to 20 results).
"""
import logging

import httpx

from app.services.recherche_provider import RecherchProviderBase, RohErgebnisData, SuchErgebnis

logger = logging.getLogger(__name__)

# Google Places API (New) base URL
PLACES_API_URL = "https://places.googleapis.com/v1/places:searchNearby"


class GooglePlacesProvider(RecherchProviderBase):
    """Google Places API (New) provider.

    Provides rich business data including:
    - Name, address, phone, website
    - Ratings, reviews count
    - Opening hours
    - Google Place ID (stable external identifier)
    """
    name = "google_places"

    def __init__(self, api_key: str):
        self._api_key = api_key

    def get_kosten_pro_request(self) -> float:
        return 0.032  # ~$0.032 per Nearby Search request

    async def ist_konfiguriert(self) -> bool:
        return bool(self._api_key)

    async def suchen(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        suchbegriff: str,
        kategorie: str | None = None,
        max_ergebnisse: int = 60,
    ) -> SuchErgebnis:
        """Search Google Places API (New) for businesses.

        Uses the Nearby Search endpoint with text query.
        Handles pagination via pageToken.
        Google doesn't return cost in the response — estimated from request count.
        """
        if not self._api_key:
            logger.warning("Google Places API key not configured, skipping.")
            return SuchErgebnis(ergebnisse=[])

        results: list[RohErgebnisData] = []
        page_token: str | None = None
        request_count = 0

        # Field mask for the response (controls billing)
        field_mask = (
            "places.id,places.displayName,places.formattedAddress,"
            "places.nationalPhoneNumber,places.internationalPhoneNumber,"
            "places.websiteUri,places.googleMapsUri,"
            "places.location,places.rating,places.userRatingCount,"
            "places.primaryType,places.types,"
            "places.regularOpeningHours"
        )

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(results) < max_ergebnisse:
                body = {
                    "locationRestriction": {
                        "circle": {
                            "center": {"latitude": lat, "longitude": lng},
                            "radius": min(radius_m, 50000),  # Max 50km
                        }
                    },
                    "maxResultCount": min(20, max_ergebnisse - len(results)),
                    "languageCode": "de",
                }

                # Add text query if we have a search term
                if suchbegriff:
                    body["includedTypes"] = []
                    # Map common German terms to Google Place types
                    type_map = {
                        "restaurant": "restaurant",
                        "café": "cafe",
                        "cafe": "cafe",
                        "bar": "bar",
                        "imbiss": "restaurant",
                        "bäckerei": "bakery",
                        "metzgerei": "butcher_shop",
                        "hotel": "hotel",
                        "apotheke": "pharmacy",
                    }
                    mapped_type = type_map.get(suchbegriff.lower())
                    if mapped_type:
                        body["includedTypes"] = [mapped_type]
                    else:
                        # Use text-based search
                        body["includedTypes"] = ["restaurant"]  # Fallback
                        # Note: Nearby Search (New) requires includedTypes

                if page_token:
                    body["pageToken"] = page_token

                headers = {
                    "Content-Type": "application/json",
                    "X-Goog-Api-Key": self._api_key,
                    "X-Goog-FieldMask": field_mask,
                }

                try:
                    response = await client.post(
                        PLACES_API_URL,
                        json=body,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()
                    request_count += 1
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"Google Places API error: {e.response.status_code} "
                        f"{e.response.text}"
                    )
                    break
                except httpx.RequestError as e:
                    logger.error(f"Google Places request error: {e}")
                    break

                places = data.get("places", [])
                if not places:
                    break

                for place in places:
                    result = self._normalize(place)
                    if result:
                        results.append(result)

                # Check for next page
                page_token = data.get("nextPageToken")
                if not page_token:
                    break

        # Google doesn't return cost — estimate from request count
        api_kosten_usd = request_count * self.get_kosten_pro_request()
        logger.info(
            f"Google Places: {len(results)} results for "
            f"'{suchbegriff}' at ({lat}, {lng}) r={radius_m}m "
            f"({request_count} requests, est. ${api_kosten_usd:.4f})"
        )
        return SuchErgebnis(ergebnisse=results, api_kosten_usd=api_kosten_usd)

    def _normalize(self, place: dict) -> RohErgebnisData | None:
        """Convert a Google Places response to normalized format."""
        display_name = place.get("displayName", {})
        name = display_name.get("text", "").strip()
        if not name:
            return None

        location = place.get("location", {})

        return RohErgebnisData(
            name=name,
            quelle="google_places",
            externe_id=place.get("id"),
            adresse=place.get("formattedAddress"),
            telefon=(
                place.get("nationalPhoneNumber")
                or place.get("internationalPhoneNumber")
            ),
            website=place.get("websiteUri"),
            kategorie=place.get("primaryType"),
            lat=location.get("latitude"),
            lng=location.get("longitude"),
            rohdaten={
                "place_id": place.get("id"),
                "rating": place.get("rating"),
                "user_rating_count": place.get("userRatingCount"),
                "types": place.get("types", []),
                "google_maps_uri": place.get("googleMapsUri"),
                "opening_hours": place.get("regularOpeningHours"),
            },
        )
