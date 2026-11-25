
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager
from app.schemas.roster_schema import (
    RosterCreate,
    RosterResponse,
    RosterGenerationRequest,
    RosterGenerationResult,
    PublishRosterRequest,
    ConflictResolutionRequest,
    RosterConflictResponse,
)
from app.models.enums import (
    RosterStatus,
    RosterPeriodStatus,
    ConflictStatus
)
from app.services import roster_service as service
from app.models.roster import Roster
from app.services.roster_generation_service import generate_roster_preview,generate_and_persist_roster

from app.schemas.roster_schema import (
    RosterGenerationResponse,
    RosterGenerationDetailResponse,
    RosterAssignmentDetailResponse,
    RosterConflictResponse,
)
from app.core.dependencies import get_current_user



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

@router.post(
    "/{roster_id}/generate-preview",
    dependencies=[Depends(require_operations_manager)]
)
def generate_roster_preview_route(
    roster_id: UUID,
    db: Session = Depends(get_db),
):
    roster = db.query(Roster).filter(
        Roster.roster_id == roster_id
    ).first()

    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    return generate_roster_preview(db, roster)
'''
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
        '''

@router.post(
    "/{roster_id}/generate-preview",
    dependencies=[Depends(require_operations_manager)]
)
def generate_roster_preview_route(
    roster_id: UUID,
    db: Session = Depends(get_db),
):
    roster = db.query(Roster).filter(
        Roster.roster_id == roster_id
    ).first()

    if not roster:
        raise HTTPException(
            status_code=404,
            detail="Roster not found"
        )

    return generate_roster_preview(db, roster)


@router.post("/{roster_id}/generate")
def generate_roster(
    roster_id: UUID,
    db: Session = Depends(get_db),
):
    roster = service.get_roster_by_id(db, roster_id)

    if not roster:
        raise HTTPException(
            status_code=404,
            detail="Roster not found",
        )

    try:
        return generate_and_persist_roster(db, roster)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Could not save roster generation due to a database conflict",
        )
        
@router.get(
    "/{roster_id}/generations",
    response_model=list[RosterGenerationResponse],
)
def get_roster_generations(
    roster_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return service.get_roster_generations(db, roster_id)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
        
        
@router.get(
    "/{roster_id}/generations/{generation_id}",
    response_model=RosterGenerationDetailResponse,
)
def get_generation_detail(
    roster_id: UUID,
    generation_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return service.get_generation_detail(
            db, roster_id, generation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{roster_id}/generations/{generation_id}/assignments",
    response_model=list[RosterAssignmentDetailResponse],
)
def get_generation_assignments(
    roster_id: UUID,
    generation_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return service.get_generation_assignments(
            db, roster_id, generation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{roster_id}/generations/{generation_id}/conflicts",
    response_model=list[RosterConflictResponse],
)
def get_generation_conflicts(
    roster_id: UUID,
    generation_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return service.get_generation_conflicts(
            db, roster_id, generation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    

@router.post("/{roster_id}/publish")
def publish_roster(
    roster_id: UUID,
    data: PublishRosterRequest,
    db: Session = Depends(get_db),
):
    try:
        return service.publish_roster(
            db=db,
            roster_id=roster_id,
            generation_id=data.generation_id,
            accept_unresolved_conflicts=data.accept_unresolved_conflicts,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch(
    "/{roster_id}/generations/{generation_id}/conflicts/{conflict_id}",
    response_model=RosterConflictResponse,
)
def resolve_conflict(
    roster_id: UUID,
    generation_id: UUID,
    conflict_id: UUID,
    data: ConflictResolutionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not current_user.employee_id:
        raise HTTPException(
            status_code=400,
            detail="Manager account must be linked to an employee",
        )

    try:
        return service.resolve_roster_conflict(
            db=db,
            roster_id=roster_id,
            generation_id=generation_id,
            conflict_id=conflict_id,
            changed_by=current_user.employee_id,
            new_status=data.status,
            notes=data.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get(
    "/{roster_id}/conflicts",
    response_model=list[RosterConflictResponse],
)
def get_roster_conflicts(
    roster_id: UUID,
    conflict_status: ConflictStatus | None = None,
    db: Session = Depends(get_db),
):
    try:
        return service.get_roster_conflicts(
            db,
            roster_id,
            conflict_status,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))