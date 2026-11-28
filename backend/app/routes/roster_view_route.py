
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user

from app.models.roster import (
    Roster,
    RosterGeneration,
    RosterEmployeeDay,
    RosterAssignment,
)
from app.models.employee import Employee
from app.models.organization import Pod, Process
from app.models.policies import Shift


router = APIRouter(
    prefix="/rosters",
    tags=["Role-Based Roster Views"],
)


def get_latest_generation(db: Session, roster: Roster):
    if roster.published_generation_id:
        generation = db.query(RosterGeneration).filter(
            RosterGeneration.generation_id
            == roster.published_generation_id,
            RosterGeneration.roster_id == roster.roster_id,
        ).first()
    else:
        generation = (
            db.query(RosterGeneration)
            .filter(RosterGeneration.roster_id == roster.roster_id)
            .order_by(RosterGeneration.generation_number.desc())
            .first()
        )

    if not generation:
        raise HTTPException(
            status_code=404,
            detail="No roster generation found",
        )

    return generation

def get_published_generation(db: Session, roster: Roster):
    if not roster.published_generation_id:
        raise HTTPException(
            status_code=403,
            detail="This roster has not been published yet",
        )

    generation = db.query(RosterGeneration).filter(
        RosterGeneration.generation_id == roster.published_generation_id,
        RosterGeneration.roster_id == roster.roster_id,
    ).first()

    if not generation:
        raise HTTPException(
            status_code=404,
            detail="Published roster generation not found",
        )

    return generation


def build_roster_response(db: Session, roster, generation, employee_ids=None):
    day_query = db.query(RosterEmployeeDay).filter(
        RosterEmployeeDay.generation_id == generation.generation_id
    )

    if employee_ids is not None:
        day_query = day_query.filter(
            RosterEmployeeDay.employee_id.in_(employee_ids)
        )

    employee_days = day_query.order_by(
        RosterEmployeeDay.roster_date
    ).all()

    result = []

    for day in employee_days:
        employee = db.query(Employee).filter(
            Employee.employee_id == day.employee_id
        ).first()

        assignments = (
            db.query(RosterAssignment, Process, Shift)
            .join(
                Process,
                RosterAssignment.process_id == Process.process_id,
            )
            .join(
                Shift,
                RosterAssignment.shift_id == Shift.shift_id,
            )
            .filter(
                RosterAssignment.employee_day_id
                == day.employee_day_id
            )
            .all()
        )

        result.append({
            "employee_day_id": str(day.employee_day_id),
            "employee_id": str(day.employee_id),
            "employee_code": employee.employee_code if employee else None,
            "employee_name": employee.full_name if employee else None,
            "roster_date": day.roster_date.isoformat(),
            "status": day.status.value,
            "notes": day.notes,
            "assignments": [
                {
                    "assignment_id": str(assignment.assignment_id),
                    "process_id": str(process.process_id),
                    "process_name": process.process_name,
                    "shift_id": str(shift.shift_id),
                    "shift_name": shift.shift_name,
                    "starts_at": assignment.starts_at.isoformat(),
                    "ends_at": assignment.ends_at.isoformat(),
                    "allocation_minutes": assignment.allocation_minutes,
                }
                for assignment, process, shift in assignments
            ],
        })

    return {
        "roster_id": str(roster.roster_id),
        "year": roster.year,
        "month": roster.month,
        "roster_status": roster.status.value,
        "generation_id": str(generation.generation_id),
        "generation_number": generation.generation_number,
        "solver_status": generation.solver_status.value,
        "employee_days": result,
    }


@router.get("/{roster_id}/view")
def get_complete_roster(
    roster_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role.value != "operations_manager":
        raise HTTPException(status_code=403, detail="Access denied")

    roster = db.query(Roster).filter(
        Roster.roster_id == roster_id
    ).first()

    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    generation = get_latest_generation(db, roster)

    return build_roster_response(db, roster, generation)


@router.get("/{roster_id}/my-pod")
def get_pod_roster(
    roster_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role.value != "pod_lead":
        raise HTTPException(status_code=403, detail="Access denied")

    if not current_user.employee_id:
        raise HTTPException(
            status_code=400,
            detail="Pod Lead account is not linked to an employee",
        )

    pod = db.query(Pod).filter(
        Pod.pod_lead_id == current_user.employee_id,
        Pod.is_active.is_(True),
    ).first()

    if not pod:
        raise HTTPException(status_code=404, detail="Assigned pod not found")

    roster = db.query(Roster).filter(
        Roster.roster_id == roster_id
    ).first()

    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    generation = get_published_generation(db, roster)

    employee_ids = [
        row[0] for row in db.query(Employee.employee_id).filter(
            Employee.pod_id == pod.pod_id
        ).all()
    ]

    response = build_roster_response(
        db, roster, generation, employee_ids
    )
    response["pod_id"] = str(pod.pod_id)
    response["pod_name"] = pod.pod_name

    return response


@router.get("/{roster_id}/my-schedule")
def get_my_schedule(
    roster_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role.value != "employee":
        raise HTTPException(status_code=403, detail="Access denied")

    if not current_user.employee_id:
        raise HTTPException(
            status_code=400,
            detail="Employee account is not linked to an employee",
        )

    roster = db.query(Roster).filter(
        Roster.roster_id == roster_id
    ).first()

    if not roster:
        raise HTTPException(status_code=404, detail="Roster not found")

    generation = get_published_generation(db, roster)

    return build_roster_response(
        db,
        roster,
        generation,
        [current_user.employee_id],
    )
