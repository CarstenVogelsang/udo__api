"""DataForSEO Business Listings provider for business data recherche.

Uses the DataForSEO Business Listings API to find businesses.
Significantly cheaper than Google Places but provides less detailed data.

API Docs: https://docs.dataforseo.com/v3/business_data/business_listings/search/live/
Pricing: ~$0.002 per result (very cost-effective for bulk recherche).
"""
import base64
import logging

import httpx

from app.services.recherche_provider import RecherchProviderBase, RohErgebnisData

logger = logging.getLogger(__name__)

DATAFORSEO_API_URL = "https://api.dataforseo.com/v3/business_data/business_listings/search/live"


class DataForSeoProvider(RecherchProviderBase):
    """DataForSEO Business Listings provider.

    Provides basic business data:
    - Name, address, phone, website
    - Category
    - Coordinates

    Less detailed than Google Places but much cheaper for bulk searches.
    """
    name = "dataforseo"

    def __init__(self, login: str, password: str):
        self._login = login
        self._password = password

    def get_kosten_pro_request(self) -> float:
        return 0.002  # ~$0.002 per result

    async def ist_konfiguriert(self) -> bool:
        return bool(self._login and self._password)

    def _auth_header(self) -> str:
        """Generate Basic Auth header value."""
        credentials = f"{self._login}:{self._password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def suchen(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        suchbegriff: str,
        kategorie: str | None = None,
        max_ergebnisse: int = 60,
    ) -> list[RohErgebnisData]:
        """Search DataForSEO Business Listings API.

        Uses location-based search with category/keyword filters.
        """
        if not self._login or not self._password:
            logger.warning("DataForSEO credentials not configured, skipping.")
            return []

        results: list[RohErgebnisData] = []

        # DataForSEO uses offset-based pagination
        offset = 0
        batch_size = min(100, max_ergebnisse)  # Max 100 per request

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(results) < max_ergebnisse:
                filters = []

                # Category filter
                if kategorie:
                    filters.append(["category", "like", f"%{kategorie}%"])

                # Location filter (coordinates + radius)
                location_filter = {
                    "latitude": lat,
                    "longitude": lng,
                    "radius": radius_m,
                }

                body = [{
                    "categories": [suchbegriff] if suchbegriff else None,
                    "location_coordinate": f"{lat},{lng},{radius_m}",
                    "language_code": "de",
                    "limit": batch_size,
                    "offset": offset,
                    "filters": filters if filters else None,
                }]

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": self._auth_header(),
                }

                try:
                    response = await client.post(
                        DATAFORSEO_API_URL,
                        json=body,
                        headers=headers,
                    )
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"DataForSEO API error: {e.response.status_code} "
                        f"{e.response.text[:500]}"
                    )
                    break
                except httpx.RequestError as e:
                    logger.error(f"DataForSEO request error: {e}")
                    break

                # Parse response
                tasks = data.get("tasks", [])
                if not tasks:
                    break

                task = tasks[0]
                if task.get("status_code") != 20000:
                    logger.error(
                        f"DataForSEO task error: {task.get('status_message')}"
                    )
                    break

                task_result = task.get("result", [])
                if not task_result:
                    break

                items = task_result[0].get("items", [])
                if not items:
                    break

                for item in items:
                    result = self._normalize(item)
                    if result:
                        results.append(result)

                # Check if more results available
                total_count = task_result[0].get("total_count", 0)
                offset += batch_size
                if offset >= total_count or len(items) < batch_size:
                    break

        logger.info(
            f"DataForSEO: {len(results)} results for "
            f"'{suchbegriff}' at ({lat}, {lng}) r={radius_m}m"
        )
        return results

    def _normalize(self, item: dict) -> RohErgebnisData | None:
        """Convert a DataForSEO Business Listing to normalized format."""
        name = (item.get("title") or "").strip()
        if not name:
            return None

        # Extract address components
        address_info = item.get("address_info", {}) or {}

        return RohErgebnisData(
            name=name,
            quelle="dataforseo",
            externe_id=item.get("cid"),
            adresse=item.get("address"),
            plz=address_info.get("zip"),
            ort=address_info.get("city"),
            telefon=item.get("phone"),
            website=item.get("url") or item.get("domain"),
            email=item.get("email"),
            kategorie=item.get("category"),
            lat=item.get("latitude"),
            lng=item.get("longitude"),
            rohdaten={
                "cid": item.get("cid"),
                "rating": item.get("rating"),
                "reviews_count": item.get("reviews_count"),
                "category_ids": item.get("category_ids", []),
                "is_claimed": item.get("is_claimed"),
            },
        )
