
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager

from app.schemas.roster_schema import (
    RosterAllocationRuleCreate,
    RosterAllocationRuleUpdate,
    RosterAllocationRuleResponse,
)

from app.services import roster_allocation_service as service


router = APIRouter(
    prefix="/roster-allocations",
    tags=["Roster Allocation Rules"],
    dependencies=[Depends(require_operations_manager)]
)


# =====================================================
# CREATE ALLOCATION RULE
# =====================================================

@router.post(
    "",
    response_model=RosterAllocationRuleResponse,
    status_code=status.HTTP_201_CREATED
)
def create_allocation_rule(
    data: RosterAllocationRuleCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_allocation_rule(db, data)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An allocation rule already exists for this employee, process and date"
        )


# =====================================================
# GET ALL ALLOCATION RULES
# =====================================================

@router.get(
    "",
    response_model=list[RosterAllocationRuleResponse]
)
def get_allocation_rules(
    roster_id: UUID | None = None,
    employee_id: UUID | None = None,
    roster_date: date | None = None,
    db: Session = Depends(get_db)
):
    return service.get_allocation_rules(
        db,
        roster_id,
        employee_id,
        roster_date
    )


# =====================================================
# GET ALLOCATION RULE BY ID
# =====================================================

@router.get(
    "/{rule_id}",
    response_model=RosterAllocationRuleResponse
)
def get_allocation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    rule = service.get_allocation_rule_by_id(db, rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation rule not found"
        )

    return rule


# =====================================================
# UPDATE ALLOCATION RULE
# =====================================================

@router.patch(
    "/{rule_id}",
    response_model=RosterAllocationRuleResponse
)
def update_allocation_rule(
    rule_id: UUID,
    data: RosterAllocationRuleUpdate,
    db: Session = Depends(get_db)
):
    rule = service.get_allocation_rule_by_id(db, rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation rule not found"
        )

    try:
        return service.update_allocation_rule(
            db, rule, data
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update allocation rule"
        )


# =====================================================
# DELETE ALLOCATION RULE
# =====================================================

@router.delete("/{rule_id}")
def delete_allocation_rule(
    rule_id: UUID,
    db: Session = Depends(get_db)
):
    rule = service.get_allocation_rule_by_id(db, rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Allocation rule not found"
        )

    try:
        return service.delete_allocation_rule(db, rule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
