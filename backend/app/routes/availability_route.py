
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager

from app.schemas.availability_schema import (
    AvailabilityRestrictionCreate,
    AvailabilityRestrictionUpdate,
    AvailabilityRestrictionResponse,
    PublicHolidayCreate,
    PublicHolidayUpdate,
    PublicHolidayResponse,
)

from app.models.enums import HolidayScope

from app.services import availability_service as service


router = APIRouter(
    prefix="/availability",
    tags=["Availability and Public Holidays"],
    dependencies=[Depends(require_operations_manager)]
)


# =====================================================
# AVAILABILITY RESTRICTION ROUTES
# =====================================================

@router.post(
    "/restrictions",
    response_model=AvailabilityRestrictionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_availability_restriction(
    data: AvailabilityRestrictionCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_availability_restriction(db, data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create availability restriction"
        )


@router.get(
    "/restrictions",
    response_model=list[AvailabilityRestrictionResponse]
)
def get_all_availability_restrictions(
    employee_id: UUID | None = None,
    restriction_date: date | None = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    return service.get_all_availability_restrictions(
        db,
        employee_id,
        restriction_date,
        active_only
    )


@router.get(
    "/restrictions/{restriction_id}",
    response_model=AvailabilityRestrictionResponse
)
def get_availability_restriction(
    restriction_id: UUID,
    db: Session = Depends(get_db)
):
    restriction = service.get_availability_restriction_by_id(
        db, restriction_id
    )

    if not restriction:
        raise HTTPException(
            status_code=404,
            detail="Availability restriction not found"
        )

    return restriction


@router.patch(
    "/restrictions/{restriction_id}",
    response_model=AvailabilityRestrictionResponse
)
def update_availability_restriction(
    restriction_id: UUID,
    data: AvailabilityRestrictionUpdate,
    db: Session = Depends(get_db)
):
    restriction = service.get_availability_restriction_by_id(
        db, restriction_id
    )

    if not restriction:
        raise HTTPException(
            status_code=404,
            detail="Availability restriction not found"
        )

    try:
        return service.update_availability_restriction(
            db, restriction, data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update availability restriction"
        )


@router.delete(
    "/restrictions/{restriction_id}",
    response_model=AvailabilityRestrictionResponse
)
def deactivate_availability_restriction(
    restriction_id: UUID,
    db: Session = Depends(get_db)
):
    restriction = service.get_availability_restriction_by_id(
        db, restriction_id
    )

    if not restriction:
        raise HTTPException(
            status_code=404,
            detail="Availability restriction not found"
        )

    return service.deactivate_availability_restriction(
        db, restriction
    )


# =====================================================
# PUBLIC HOLIDAY ROUTES
# =====================================================

@router.post(
    "/holidays",
    response_model=PublicHolidayResponse,
    status_code=status.HTTP_201_CREATED
)
def create_public_holiday(
    data: PublicHolidayCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_public_holiday(db, data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to create public holiday"
        )


@router.get(
    "/holidays",
    response_model=list[PublicHolidayResponse]
)
def get_all_public_holidays(
    holiday_date: date | None = None,
    scope: HolidayScope | None = None,
    brand_id: UUID | None = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    return service.get_all_public_holidays(
        db,
        holiday_date,
        scope,
        brand_id,
        active_only
    )


@router.get(
    "/holidays/{holiday_id}",
    response_model=PublicHolidayResponse
)
def get_public_holiday(
    holiday_id: UUID,
    db: Session = Depends(get_db)
):
    holiday = service.get_public_holiday_by_id(
        db, holiday_id
    )

    if not holiday:
        raise HTTPException(
            status_code=404,
            detail="Public holiday not found"
        )

    return holiday


@router.patch(
    "/holidays/{holiday_id}",
    response_model=PublicHolidayResponse
)
def update_public_holiday(
    holiday_id: UUID,
    data: PublicHolidayUpdate,
    db: Session = Depends(get_db)
):
    holiday = service.get_public_holiday_by_id(
        db, holiday_id
    )

    if not holiday:
        raise HTTPException(
            status_code=404,
            detail="Public holiday not found"
        )

    try:
        return service.update_public_holiday(
            db, holiday, data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Unable to update public holiday"
        )


@router.delete(
    "/holidays/{holiday_id}",
    response_model=PublicHolidayResponse
)
def deactivate_public_holiday(
    holiday_id: UUID,
    db: Session = Depends(get_db)
):
    holiday = service.get_public_holiday_by_id(
        db, holiday_id
    )

    if not holiday:
        raise HTTPException(
            status_code=404,
            detail="Public holiday not found"
        )

    return service.deactivate_public_holiday(
        db, holiday
    )
