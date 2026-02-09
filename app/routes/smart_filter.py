"""
API Routes for Smart Filter management.

Provides CRUD for saved filter definitions and a validation endpoint.
All endpoints are only accessible by superadmin users.
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import require_superadmin
from app.models.partner import ApiPartner
from app.services.smart_filter import SmartFilterService
from app.services.smart_filter_parser import (
    SmartFilterError,
    validate_dsl,
    parse_unternehmen_filter,
    get_unternehmen_field_map,
    get_unternehmen_relation_map,
)
from app.services.com import ComService
from app.schemas.smart_filter import (
    SmartFilterCreate,
    SmartFilterUpdate,
    SmartFilterResponse,
    SmartFilterList,
    SmartFilterValidateRequest,
    SmartFilterValidateResponse,
)

router = APIRouter(prefix="/smart-filters", tags=["Smart Filters"])


# ── Entity-type DSL config registry ──────────────────────────────────────

DSL_CONFIGS = {
    "unternehmen": {
        "field_map_fn": get_unternehmen_field_map,
        "relation_map_fn": get_unternehmen_relation_map,
    },
}


def _get_dsl_config(entity_type: str) -> dict:
    """Get the DSL field/relation maps for an entity type."""
    config = DSL_CONFIGS.get(entity_type)
    if not config:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown entity type: {entity_type}. Supported: {', '.join(DSL_CONFIGS.keys())}",
        )
    return {
        "field_map": config["field_map_fn"](),
        "relation_map": config["relation_map_fn"](),
    }


# ── CRUD Endpoints ───────────────────────────────────────────────────────

@router.get("", response_model=SmartFilterList)
async def list_filters(
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
    entity_type: str | None = Query(None, description="Filter by entity type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """List all smart filters, optionally filtered by entity type."""
    service = SmartFilterService(db)
    return await service.get_filters(entity_type=entity_type, skip=skip, limit=limit)


@router.post("", response_model=SmartFilterResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(
    data: SmartFilterCreate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new smart filter.

    The DSL expression is validated before saving.
    """
    # Validate DSL before saving
    config = _get_dsl_config(data.entity_type)
    result = validate_dsl(data.dsl_expression, config["field_map"], config["relation_map"])
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=f"Invalid DSL: {result['error']}")

    service = SmartFilterService(db)
    return await service.create_filter(data)


@router.get("/{filter_id}", response_model=SmartFilterResponse)
async def get_filter(
    filter_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single smart filter by ID."""
    service = SmartFilterService(db)
    smart_filter = await service.get_filter_by_id(filter_id)
    if not smart_filter:
        raise HTTPException(status_code=404, detail="Smart Filter nicht gefunden")
    return smart_filter


@router.patch("/{filter_id}", response_model=SmartFilterResponse)
async def update_filter(
    filter_id: str,
    data: SmartFilterUpdate,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a smart filter.

    If dsl_expression is provided, it is validated before saving.
    """
    if data.dsl_expression:
        # Need to know the entity_type — get existing filter first
        service = SmartFilterService(db)
        existing = await service.get_filter_by_id(filter_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Smart Filter nicht gefunden")

        config = _get_dsl_config(existing.entity_type)
        result = validate_dsl(data.dsl_expression, config["field_map"], config["relation_map"])
        if not result["valid"]:
            raise HTTPException(status_code=400, detail=f"Invalid DSL: {result['error']}")

    service = SmartFilterService(db)
    smart_filter = await service.update_filter(filter_id, data)
    if not smart_filter:
        raise HTTPException(status_code=404, detail="Smart Filter nicht gefunden")
    return smart_filter


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    filter_id: str,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a smart filter."""
    service = SmartFilterService(db)
    deleted = await service.delete_filter(filter_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Smart Filter nicht gefunden")


# ── Validation Endpoint ──────────────────────────────────────────────────

@router.post("/validate", response_model=SmartFilterValidateResponse)
async def validate_filter(
    data: SmartFilterValidateRequest,
    admin: ApiPartner = Depends(require_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """
    Validate a DSL expression and return the number of matching records.

    Does not save anything — this is for testing DSL expressions before saving.
    """
    config = _get_dsl_config(data.entity_type)
    result = validate_dsl(data.dsl_expression, config["field_map"], config["relation_map"])

    if not result["valid"]:
        return SmartFilterValidateResponse(valid=False, error=result["error"])

    # Count matching records
    try:
        if data.entity_type == "unternehmen":
            condition = parse_unternehmen_filter(data.dsl_expression)
            com_service = ComService(db)
            data_result = await com_service.get_unternehmen_list(
                filter_conditions=[condition],
                limit=0,
            )
            return SmartFilterValidateResponse(valid=True, count=data_result["total"])
    except SmartFilterError as e:
        return SmartFilterValidateResponse(valid=False, error=str(e))

    return SmartFilterValidateResponse(valid=True)
