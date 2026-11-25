
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.roster import Roster,RosterGeneration
from app.models.enums import RosterStatus, RosterPeriodStatus,GenerationStatus,ConflictStatus
from app.schemas.roster_schema import RosterGenerationResponse
from app.models.roster import (
    Roster,
    RosterGeneration,
    RosterAssignment,
    RosterConflict,
    RosterConflictHistory
)
from datetime import datetime, timezone
from app.models.employee import Employee
from app.models.organization import Process
from app.models.policies import Shift


def create_roster(db: Session, data):
    existing = db.query(Roster).filter(
        Roster.year == data.year,
        Roster.month == data.month
    ).first()

    if existing:
        raise ValueError(
            "A roster already exists for this month and year"
        )

    roster = Roster(
        year=data.year,
        month=data.month,
        status=RosterStatus.DRAFT,
        period_status=RosterPeriodStatus.ACTIVE
    )

    db.add(roster)
    db.commit()
    db.refresh(roster)

    return roster


def get_all_rosters(
    db: Session,
    year: int | None = None,
    month: int | None = None,
    status: RosterStatus | None = None,
    period_status: RosterPeriodStatus | None = None
):
    query = db.query(Roster)

    if year is not None:
        query = query.filter(Roster.year == year)

    if month is not None:
        query = query.filter(Roster.month == month)

    if status is not None:
        query = query.filter(Roster.status == status)

    if period_status is not None:
        query = query.filter(Roster.period_status == period_status)

    return query.order_by(
        Roster.year.desc(),
        Roster.month.desc()
    ).all()


def get_roster_by_id(db: Session, roster_id: UUID):
    return db.query(Roster).filter(
        Roster.roster_id == roster_id
    ).first()


def archive_roster(db: Session, roster: Roster):
    if roster.period_status == RosterPeriodStatus.ARCHIVED:
        raise ValueError("Roster is already archived")

    roster.period_status = RosterPeriodStatus.ARCHIVED

    db.commit()
    db.refresh(roster)

    return roster

def get_roster_generations(db: Session, roster_id: UUID):
    roster = get_roster_by_id(db, roster_id)

    if not roster:
        raise ValueError("Roster not found")

    return (
        db.query(RosterGeneration)
        .filter(RosterGeneration.roster_id == roster_id)
        .order_by(RosterGeneration.generation_number.desc())
        .all()
    )
    
def _get_generation(db: Session, roster_id: UUID, generation_id: UUID):
    roster = get_roster_by_id(db, roster_id)

    if not roster:
        raise ValueError("Roster not found")

    generation = (
        db.query(RosterGeneration)
        .filter(
            RosterGeneration.generation_id == generation_id,
            RosterGeneration.roster_id == roster_id,
        )
        .first()
    )

    if not generation:
        raise ValueError("Roster generation not found")

    return generation


def get_generation_detail(
    db: Session,
    roster_id: UUID,
    generation_id: UUID,
):
    generation = _get_generation(db, roster_id, generation_id)

    total_assignments = (
        db.query(RosterAssignment)
        .filter(
            RosterAssignment.generation_id == generation_id
        )
        .count()
    )

    total_conflicts = (
        db.query(RosterConflict)
        .filter(
            RosterConflict.generation_id == generation_id
        )
        .count()
    )

    return {
        "generation_id": generation.generation_id,
        "roster_id": generation.roster_id,
        "generation_number": generation.generation_number,
        "solver_status": generation.solver_status,
        "solver_time_limit_seconds": generation.solver_time_limit_seconds,
        "solver_parameters": generation.solver_parameters,
        "objective_value": generation.objective_value,
        "started_at": generation.started_at,
        "completed_at": generation.completed_at,
        "created_at": generation.created_at,
        "total_assignments": total_assignments,
        "total_conflicts": total_conflicts,
    }


def get_generation_assignments(
    db: Session,
    roster_id: UUID,
    generation_id: UUID,
):
    _get_generation(db, roster_id, generation_id)

    rows = (
        db.query(
            RosterAssignment,
            Employee.full_name.label("employee_name"),
            Process.process_name.label("process_name"),
            Shift.shift_name.label("shift_name"),
        )
        .join(
            Employee,
            RosterAssignment.employee_id == Employee.employee_id,
        )
        .join(
            Process,
            RosterAssignment.process_id == Process.process_id,
        )
        .join(
            Shift,
            RosterAssignment.shift_id == Shift.shift_id,
        )
        .filter(
            RosterAssignment.generation_id == generation_id
        )
        .order_by(
            RosterAssignment.starts_at,
            Employee.full_name,
        )
        .all()
    )

    return [
        {
            "assignment_id": assignment.assignment_id,
            "generation_id": assignment.generation_id,
            "employee_day_id": assignment.employee_day_id,
            "employee_id": assignment.employee_id,
            "process_id": assignment.process_id,
            "shift_id": assignment.shift_id,
            "starts_at": assignment.starts_at,
            "ends_at": assignment.ends_at,
            "allocation_minutes": assignment.allocation_minutes,
            "employee_name": employee_name,
            "process_name": process_name,
            "shift_name": shift_name,
        }
        for assignment, employee_name, process_name, shift_name in rows
    ]


def get_generation_conflicts(
    db: Session,
    roster_id: UUID,
    generation_id: UUID,
):
    _get_generation(db, roster_id, generation_id)

    return (
        db.query(RosterConflict)
        .filter(
            RosterConflict.generation_id == generation_id
        )
        .order_by(
            RosterConflict.conflict_date,
            RosterConflict.created_at,
        )
        .all()
    )
    
    
def publish_roster(
    db: Session,
    roster_id: UUID,
    generation_id: UUID,
    accept_unresolved_conflicts: bool,
):
    roster = get_roster_by_id(db, roster_id)

    if not roster:
        raise ValueError("Roster not found")

    if roster.status != RosterStatus.DRAFT:
        raise ValueError("Only draft rosters can be published")

    if roster.period_status != RosterPeriodStatus.ACTIVE:
        raise ValueError("Archived rosters cannot be published")

    generation = (
        db.query(RosterGeneration)
        .filter(
            RosterGeneration.generation_id == generation_id,
            RosterGeneration.roster_id == roster_id,
        )
        .first()
    )

    if not generation:
        raise ValueError("Roster generation not found")

    if generation.solver_status not in (
        GenerationStatus.OPTIMAL,
        GenerationStatus.FEASIBLE,
    ):
        raise ValueError("Only feasible generations can be published")

    open_conflicts = (
        db.query(RosterConflict)
        .filter(
            RosterConflict.generation_id == generation_id,
            RosterConflict.status == ConflictStatus.OPEN,
        )
        .count()
    )

    if open_conflicts and not accept_unresolved_conflicts:
        raise ValueError(
            f"{open_conflicts} unresolved conflicts exist. "
            "Review them before publishing or explicitly accept them."
        )

    try:
        roster.published_generation_id = generation_id
        roster.status = RosterStatus.PUBLISHED
        roster.published_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(roster)

        return {
            "message": "Roster published successfully",
            "roster_id": str(roster.roster_id),
            "generation_id": str(generation_id),
            "published_at": roster.published_at,
            "unresolved_conflicts": open_conflicts,
        }

    except Exception:
        db.rollback()
        raise


def resolve_roster_conflict(
    db: Session,
    roster_id: UUID,
    generation_id: UUID,
    conflict_id: UUID,
    changed_by: UUID,
    new_status: ConflictStatus,
    notes: str | None = None,
):
    if new_status not in (
        ConflictStatus.RESOLVED,
        ConflictStatus.IGNORED,
    ):
        raise ValueError("Conflict can only be resolved or ignored")

    _get_generation(db, roster_id, generation_id)

    conflict = (
        db.query(RosterConflict)
        .filter(
            RosterConflict.conflict_id == conflict_id,
            RosterConflict.generation_id == generation_id,
        )
        .first()
    )

    if not conflict:
        raise ValueError("Conflict not found")

    if conflict.status != ConflictStatus.OPEN:
        raise ValueError("Only open conflicts can be updated")

    try:
        previous_status = conflict.status
        now = datetime.now(timezone.utc)

        conflict.status = new_status
        conflict.resolution_notes = notes
        conflict.resolved_by = changed_by
        conflict.resolved_at = now

        db.add(
            RosterConflictHistory(
                conflict_id=conflict.conflict_id,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=changed_by,
                notes=notes,
            )
        )

        db.commit()
        db.refresh(conflict)

        return conflict

    except Exception:
        db.rollback()
        raise
    

def get_roster_conflicts(
    db: Session,
    roster_id: UUID,
    conflict_status: ConflictStatus | None = None,
):
    roster = get_roster_by_id(db, roster_id)

    if not roster:
        raise ValueError("Roster not found")

    query = (
        db.query(RosterConflict)
        .join(
            RosterGeneration,
            RosterConflict.generation_id == RosterGeneration.generation_id,
        )
        .filter(RosterGeneration.roster_id == roster_id)
    )

    if conflict_status:
        query = query.filter(
            RosterConflict.status == conflict_status
        )

    return query.order_by(
        RosterConflict.conflict_date,
        RosterConflict.created_at,
    ).all()
