
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager

from app.schemas.roster_schema import (
    RosterCreate,
    RosterResponse
)

from app.models.roster import Roster
from app.models.enums import (
    RosterStatus,
    RosterPeriodStatus
)

from app.services import roster_service as service


router = APIRouter(
    prefix="/rosters",
    tags=["Roster Management"],
    dependencies=[Depends(require_operations_manager)]
)


@router.post(
    "",
    response_model=RosterResponse,
    status_code=status.HTTP_201_CREATED
)
def create_roster(
    data: RosterCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_roster(db, data)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A roster already exists for this month and year"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get(
    "",
    response_model=list[RosterResponse]
)
def get_all_rosters(
    year: int | None = None,
    month: int | None = None,
    roster_status: RosterStatus | None = None,
    period_status: RosterPeriodStatus | None = None,
    db: Session = Depends(get_db)
):
    return service.get_all_rosters(
        db,
        year,
        month,
        roster_status,
        period_status
    )


@router.get(
    "/{roster_id}",
    response_model=RosterResponse
)
def get_roster(
    roster_id: UUID,
    db: Session = Depends(get_db)
):
    roster = service.get_roster_by_id(db, roster_id)

    if not roster:
        raise HTTPException(
            status_code=404,
            detail="Roster not found"
        )

    return roster


@router.patch(
    "/{roster_id}/archive",
    response_model=RosterResponse
)
def archive_roster(
    roster_id: UUID,
    db: Session = Depends(get_db)
):
    roster = service.get_roster_by_id(db, roster_id)

    if not roster:
        raise HTTPException(
            status_code=404,
            detail="Roster not found"
        )

    try:
        return service.archive_roster(db, roster)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
