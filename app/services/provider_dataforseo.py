"""DataForSEO Business Listings provider for business data recherche.

Uses the DataForSEO Business Listings API to find businesses.
Significantly cheaper than Google Places but provides less detailed data.

API Docs: https://docs.dataforseo.com/v3/business_data/business_listings/search/live/
Pricing: ~$0.002 per result (very cost-effective for bulk recherche).
"""
import base64
import json
import logging

import httpx

from app.services.recherche_provider import RecherchProviderBase, RohErgebnisData, SuchErgebnis

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
    ) -> SuchErgebnis:
        """Search DataForSEO Business Listings API.

        Uses location-based search with category/keyword filters.
        Returns results with actual API cost from the response.
        """
        if not self._login or not self._password:
            logger.warning("DataForSEO credentials not configured, skipping.")
            return SuchErgebnis(ergebnisse=[])

        results: list[RohErgebnisData] = []
        raw_items_all: list[dict] = []
        api_kosten_usd = 0.0

        # DataForSEO uses offset-based pagination
        offset = 0
        batch_size = min(100, max_ergebnisse)  # Max 100 per request

        # Convert radius from meters to kilometers (API expects km, min 1km)
        radius_km = max(1, round(radius_m / 1000))

        async with httpx.AsyncClient(timeout=30.0) as client:
            while len(results) < max_ergebnisse:
                filters = []

                # Category filter (additional to categories param)
                if kategorie:
                    filters.append(["category", "like", f"%{kategorie}%"])

                # Build request body per DataForSEO docs:
                # https://docs.dataforseo.com/v3/business_data/business_listings/search/live/
                # Only include parameters that have values (no None/null).
                task = {
                    "categories": [suchbegriff.lower()] if suchbegriff else ["restaurant"],
                    "location_coordinate": f"{lat},{lng},{radius_km}",
                    "limit": batch_size,
                }

                # offset only when paginating (default is 0)
                if offset > 0:
                    task["offset"] = offset

                if filters:
                    task["filters"] = filters

                body = [task]
                logger.info(f"DataForSEO request: {json.dumps(body, ensure_ascii=False)}")

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
                api_kosten_usd += task.get("cost", 0) or 0

                if task.get("status_code") != 20000:
                    logger.error(
                        f"DataForSEO task error (code={task.get('status_code')}): "
                        f"{task.get('status_message')}\n"
                        f"Full task response: {json.dumps(task, indent=2, ensure_ascii=False)}"
                    )
                    break

                task_result = task.get("result", [])
                if not task_result:
                    break

                items = task_result[0].get("items", [])
                if not items:
                    break

                for item in items:
                    raw_items_all.append(item)

                    # Log first raw item for debugging
                    if not results:
                        logger.info(
                            f"DataForSEO sample item (raw):\n"
                            f"{json.dumps(item, indent=2, ensure_ascii=False)}"
                        )

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
            f"'{suchbegriff}' at ({lat}, {lng}) r={radius_km}km "
            f"(API cost: ${api_kosten_usd:.4f})"
        )
        return SuchErgebnis(
            ergebnisse=results,
            api_kosten_usd=api_kosten_usd,
            raw_items=raw_items_all,
        )

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
            rohdaten=item,
        )
