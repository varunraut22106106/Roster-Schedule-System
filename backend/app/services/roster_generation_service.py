
import calendar
from datetime import date, datetime, time, timedelta
from app.models.enums import StaffingRuleScope
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.enums import AllocationMode

from app.models.employee import Employee, EmployeeAssignment
from app.models.organization import Brand, Pod, Process
from app.models.policies import (
    Shift,
    ProcessOperatingDay,
    StaffingRequirement,
    WeeklyOffPolicy,
    WorkloadPolicy,
)
from app.models.availability import (
    PublicHoliday,
    Leave,
    CompOffTransaction,
    AvailabilityRestriction,
)
from app.models.roster import (
    Roster,
    RosterGeneration,
    RosterEmployeeDay,
    RosterAssignment,
    RosterConflict,
    RosterAllocationRule,
)
from app.models.enums import (
    EmployeeStatus,
    AssignmentStatus,
    LeaveStatus,
    AvailabilityType,
    HolidayScope,
    CompOffStatus,
    CompOffAction,
    DayStatus,
    GenerationStatus,
    RosterStatus,
    RosterPeriodStatus,
    ConflictType,
)

from app.engine.roster_engine import (
    AssignmentOption,
    StaffingSlot,
    EmployeeLimit,
    UnavailablePeriod,
    solve_roster,
)


def get_roster_dates(year: int, month: int):
    start_date = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    end_date = date(year, month, last_day)

    dates = []
    current = start_date

    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    return dates


def combine_shift_times(work_date: date, start_time: time, end_time: time):
    starts_at = datetime.combine(work_date, start_time)
    ends_at = datetime.combine(work_date, end_time)

    # Support overnight shifts.
    if ends_at <= starts_at:
        ends_at += timedelta(days=1)

    return starts_at, ends_at



def build_candidate_options(db: Session, roster: Roster):
    dates = get_roster_dates(roster.year, roster.month)

    employees = db.query(Employee).filter(
        Employee.status == EmployeeStatus.ACTIVE
    ).all()

    shifts = db.query(Shift).filter(
        Shift.is_active.is_(True)
    ).all()
    print(f"Active shifts found: {len(shifts)}")
    options = []

    for employee in employees:
        assignments = (
            db.query(EmployeeAssignment)
            .join(Process, EmployeeAssignment.process_id == Process.process_id)
            .join(Brand, Process.brand_id == Brand.brand_id)
            .filter(
                EmployeeAssignment.employee_id == employee.employee_id,
                EmployeeAssignment.status == AssignmentStatus.ACTIVE,
                Process.is_active.is_(True),
                Brand.is_active.is_(True),
                EmployeeAssignment.start_date <= dates[-1],
                (
                    EmployeeAssignment.end_date.is_(None)
                    | (EmployeeAssignment.end_date >= dates[0])
                ),
            )
            .all()
        )
        
        print(f"\nEmployee: {employee.employee_code}")
        print(f"Employee ID: {employee.employee_id}")
        print(f"Assignments found: {len(assignments)}")


        for assignment in assignments:
            print(
            f"Process: {assignment.process_id}, "
            f"Start: {assignment.start_date}, "
            f"End: {assignment.end_date}, "
            f"Status: {assignment.status}"
        )
            for work_date in dates:
                if not (
                    assignment.start_date <= work_date
                    and (
                        assignment.end_date is None
                        or assignment.end_date >= work_date
                    )
                ):
                    continue

                rules = (
                    db.query(RosterAllocationRule)
                    .filter(
                        RosterAllocationRule.roster_id == roster.roster_id,
                        RosterAllocationRule.employee_id == employee.employee_id,
                        RosterAllocationRule.process_id == assignment.process_id,
                        RosterAllocationRule.roster_date == work_date,
                    )
                    .first()
                )

                for shift in shifts:
                    starts_at, ends_at = combine_shift_times(
                        work_date,
                        shift.start_time,
                        shift.end_time,
                    )

                    shift_minutes = int(
                        (ends_at - starts_at).total_seconds() // 60
                    )

                    if rules is None:
                        minimum_minutes = shift_minutes
                        maximum_minutes = shift_minutes
                        fixed_minutes = shift_minutes

                    elif rules.allocation_mode == AllocationMode.FIXED:
                        fixed_minutes = rules.fixed_minutes

                        if fixed_minutes > shift_minutes:
                            raise ValueError(
                                f"Allocation exceeds shift duration for "
                                f"employee {employee.employee_code} "
                                f"on {work_date}"
                            )

                        minimum_minutes = fixed_minutes
                        maximum_minutes = fixed_minutes

                    else:
                        minimum_minutes = rules.minimum_minutes
                        maximum_minutes = rules.maximum_minutes
                        fixed_minutes = None

                        if maximum_minutes > shift_minutes:
                            raise ValueError(
                                f"Maximum allocation exceeds shift duration "
                                f"for employee {employee.employee_code} "
                                f"on {work_date}"
                            )

                    options.append(
                        AssignmentOption(
                            employee_id=employee.employee_id,
                            process_id=assignment.process_id,
                            shift_id=shift.shift_id,
                            work_date=work_date,
                            starts_at=starts_at,
                            ends_at=ends_at,
                            minimum_minutes=minimum_minutes,
                            maximum_minutes=maximum_minutes,
                            fixed_minutes=fixed_minutes,
                        )
                    )

    return employees, options


def build_employee_limits(db: Session, employees, roster: Roster):
    start_date = date(roster.year, roster.month, 1)

    policy = (
        db.query(WorkloadPolicy)
        .filter(
            WorkloadPolicy.is_active.is_(True),
            WorkloadPolicy.effective_from <= start_date,
            (
                WorkloadPolicy.effective_until.is_(None)
                | (WorkloadPolicy.effective_until >= start_date)
            ),
        )
        .order_by(WorkloadPolicy.effective_from.desc())
        .first()
    )

    if policy is None:
        return []

    # The current solver accepts whole-hour workload limits.
    hour_values = [
        policy.max_hours_per_day,
        policy.max_hours_per_week,
        policy.minimum_rest_hours,
    ]

    if any(value % 1 != 0 for value in hour_values):
        raise ValueError(
            "Current solver expects whole-hour workload policies. "
            "Decimal-hour support needs a minutes-based engine update."
        )

    return [
        EmployeeLimit(
            employee_id=employee.employee_id,
            max_hours_per_day=int(policy.max_hours_per_day),
            max_hours_per_week=int(policy.max_hours_per_week),
            max_work_days_per_week=policy.max_work_days_per_week,
            max_consecutive_work_days=policy.max_consecutive_work_days,
            minimum_rest_hours=int(policy.minimum_rest_hours),
        )
        for employee in employees
    ]


def build_staffing_slots(db: Session, roster: Roster):
    dates = get_roster_dates(roster.year, roster.month)

    requirements = db.query(StaffingRequirement).filter(
        StaffingRequirement.is_active.is_(True)
    ).all()

    shifts = {
        shift.shift_id: shift
        for shift in db.query(Shift).filter(
            Shift.is_active.is_(True)
        ).all()
    }

    operating_days = db.query(ProcessOperatingDay).all()
    operating_map = {
        (item.process_id, item.weekday): item.is_operating
        for item in operating_days
    }

    processes = db.query(Process).join(
        Brand, Process.brand_id == Brand.brand_id
    ).filter(
        Process.is_active.is_(True),
        Brand.is_active.is_(True),
    ).all()

    holidays = db.query(PublicHoliday).filter(
        PublicHoliday.is_active.is_(True),
        PublicHoliday.holiday_date >= dates[0],
        PublicHoliday.holiday_date <= dates[-1],
    ).all()

    holiday_map = {
        (holiday.holiday_date, holiday.scope, holiday.brand_id)
        for holiday in holidays
    }

    slots = []

    for process in processes:
        for work_date in dates:

            if operating_map.get(
                (process.process_id, work_date.weekday()), True
            ) is False:
                continue

            if (
                (work_date, HolidayScope.ORGANIZATION, None) in holiday_map
                or
                (work_date, HolidayScope.BRAND, process.brand_id) in holiday_map
            ):
                continue

            applicable = []

            for requirement in requirements:
                if requirement.process_id != process.process_id:
                    continue

                if requirement.scope == StaffingRuleScope.DATE:
                    if requirement.effective_date != work_date:
                        continue
                    priority = 3

                elif requirement.scope == StaffingRuleScope.WEEKDAY:
                    if requirement.weekday != work_date.weekday():
                        continue
                    priority = 2

                else:
                    priority = 1

                applicable.append((priority, requirement))

            # Select the most specific rule for each shift/time-slot pair.
            groups = {}

            for priority, requirement in applicable:
                key = (
                    requirement.shift_id,
                    requirement.start_time,
                    requirement.end_time,
                )

                if key not in groups or priority > groups[key][0]:
                    groups[key] = (priority, requirement)

            for _, requirement in groups.values():
                if requirement.shift_id is not None:
                    shift = shifts.get(requirement.shift_id)

                    if shift is None:
                        continue

                    starts_at, ends_at = combine_shift_times(
                        work_date,
                        shift.start_time,
                        shift.end_time,
                    )

                elif (
                    requirement.start_time is not None
                    and requirement.end_time is not None
                ):
                    starts_at, ends_at = combine_shift_times(
                        work_date,
                        requirement.start_time,
                        requirement.end_time,
                    )

                else:
                    raise ValueError(
                        f"Staffing requirement {requirement.requirement_id} "
                        "has no shift or time-slot definition."
                    )

                slots.append(
                    StaffingSlot(
                        process_id=process.process_id,
                        work_date=work_date,
                        starts_at=starts_at,
                        ends_at=ends_at,
                        minimum_employees=requirement.minimum_employees,
                        shift_id=requirement.shift_id,
                    )
                )

    return slots


def build_unavailable_periods(db: Session, employees, roster: Roster):
    dates = get_roster_dates(roster.year, roster.month)

    employee_ids = [employee.employee_id for employee in employees]

    if not employee_ids:
        return []

    unavailable = []

    leaves = db.query(Leave).filter(
        Leave.employee_id.in_(employee_ids),
        Leave.status.in_([
            LeaveStatus.PENDING,
            LeaveStatus.APPROVED,
        ]),
        Leave.start_date <= dates[-1],
        Leave.end_date >= dates[0],
    ).all()

    for leave in leaves:
        start_date = max(leave.start_date, dates[0])
        end_date = min(leave.end_date, dates[-1])

        unavailable.append(
            UnavailablePeriod(
                employee_id=leave.employee_id,
                starts_at=datetime.combine(start_date, time.min),
                ends_at=datetime.combine(
                    end_date + timedelta(days=1), time.min
                ),
            )
        )

    restrictions = db.query(AvailabilityRestriction).filter(
        AvailabilityRestriction.employee_id.in_(employee_ids),
        AvailabilityRestriction.is_active.is_(True),
        AvailabilityRestriction.restriction_date >= dates[0],
        AvailabilityRestriction.restriction_date <= dates[-1],
    ).all()

    for restriction in restrictions:
        if restriction.restriction_type == AvailabilityType.FULL_DAY:
            starts_at = datetime.combine(
                restriction.restriction_date, time.min
            )
            ends_at = starts_at + timedelta(days=1)
        else:
            if (
                restriction.start_time is None
                or restriction.end_time is None
            ):
                raise ValueError(
                    f"Time-slot restriction {restriction.restriction_id} "
                    "is missing its start or end time."
                )

            starts_at, ends_at = combine_shift_times(
                restriction.restriction_date,
                restriction.start_time,
                restriction.end_time,
            )

        unavailable.append(
            UnavailablePeriod(
                employee_id=restriction.employee_id,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        )

    comp_offs = db.query(CompOffTransaction).filter(
        CompOffTransaction.employee_id.in_(employee_ids),
        CompOffTransaction.action == CompOffAction.USE_APPROVED,
        CompOffTransaction.status == CompOffStatus.APPROVED,
        CompOffTransaction.requested_date >= dates[0],
        CompOffTransaction.requested_date <= dates[-1],
    ).all()

    for comp_off in comp_offs:
        starts_at = datetime.combine(comp_off.requested_date, time.min)

        unavailable.append(
            UnavailablePeriod(
                employee_id=comp_off.employee_id,
                starts_at=starts_at,
                ends_at=starts_at + timedelta(days=1),
            )
        )

    return unavailable

def generate_roster_preview(
    db: Session,
    roster: Roster,
):
    if roster.status != RosterStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft rosters can be generated",
        )

    if roster.period_status != RosterPeriodStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Archived roster periods cannot be generated",
        )

    try:
        # Build solver inputs
        employees, options = build_candidate_options(db, roster)

        employee_limits = build_employee_limits(
            db, employees, roster
        )

        staffing_slots = build_staffing_slots(db, roster)

        unavailable_periods = build_unavailable_periods(
            db, employees, roster
        )

        # Run OR-Tools
        result = solve_roster(
            options=options,
            staffing_slots=staffing_slots,
            employee_limits=employee_limits,
            unavailable_periods=unavailable_periods,
            time_limit_seconds=30,
            relax_coverage=True,
        )

        return {
            "roster_id": str(roster.roster_id),
            "solver_status": result.status,
            "objective_value": result.objective_value,
            "solver_time_seconds": result.solver_time_seconds,
            "total_employees": len(employees),
            "total_options": len(options),
            "total_staffing_slots": len(staffing_slots),
            "total_assignments": len(result.assignments),
            "unmet_coverage": result.unmet_coverage,
            "assignments": [
                {
                    "employee_id": str(a["employee_id"]),
                    "process_id": str(a["process_id"]),
                    "shift_id": str(a["shift_id"]),
                    "work_date": a["work_date"].isoformat(),
                    "starts_at": a["starts_at"].isoformat(),
                    "ends_at": a["ends_at"].isoformat(),
                    "allocation_minutes": a["allocation_minutes"],
                }
                for a in result.assignments
            ],
        }

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    
    
from datetime import timezone
from app.models.enums import ConflictStatus


def persist_roster_generation(
    db: Session,
    roster: Roster,
    result,
    time_limit_seconds: int = 30,
):
    if roster.status != RosterStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft rosters can be generated",
        )

    if roster.period_status != RosterPeriodStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Archived roster periods cannot be generated",
        )

    if result.status not in ("OPTIMAL", "FEASIBLE"):
        raise HTTPException(
            status_code=422,
            detail=f"Cannot persist roster. Solver status: {result.status}",
        )

    try:
        latest_generation = (
            db.query(func.max(RosterGeneration.generation_number))
            .filter(RosterGeneration.roster_id == roster.roster_id)
            .scalar()
        )

        generation_number = (latest_generation or 0) + 1
        completed_at = datetime.now(timezone.utc)

        generation = RosterGeneration(
            roster_id=roster.roster_id,
            generation_number=generation_number,
            solver_status=GenerationStatus(result.status.lower()),
            solver_time_limit_seconds=time_limit_seconds,
            solver_parameters={
                "time_limit_seconds": time_limit_seconds,
                "coverage_relaxation": True,
            },
            objective_value=result.objective_value,
            started_at=completed_at - timedelta(
                seconds=result.solver_time_seconds
            ),
            completed_at=completed_at,
        )

        db.add(generation)
        db.flush()

        # Create one employee-day record for each scheduled employee/date.
        employee_dates = {
            (a["employee_id"], a["work_date"])
            for a in result.assignments
        }

        employee_day_map = {}

        for employee_id, work_date in employee_dates:
            employee_day = RosterEmployeeDay(
                generation_id=generation.generation_id,
                employee_id=employee_id,
                roster_date=work_date,
                status=DayStatus.WORKING,
            )

            db.add(employee_day)
            db.flush()

            employee_day_map[(employee_id, work_date)] = (
                employee_day.employee_day_id
            )

        # Save assignments.
        for assignment in result.assignments:
            employee_day_id = employee_day_map[
                (assignment["employee_id"], assignment["work_date"])
            ]

            db.add(
                RosterAssignment(
                    generation_id=generation.generation_id,
                    employee_day_id=employee_day_id,
                    employee_id=assignment["employee_id"],
                    process_id=assignment["process_id"],
                    shift_id=assignment["shift_id"],
                    starts_at=assignment["starts_at"].replace(
                        tzinfo=timezone.utc
                    ),
                    ends_at=assignment["ends_at"].replace(
                        tzinfo=timezone.utc
                    ),
                    allocation_minutes=assignment["allocation_minutes"],
                )
            )

        # Save unmet staffing coverage as conflicts.
        for gap in result.unmet_coverage:
            db.add(
                RosterConflict(
                    generation_id=generation.generation_id,
                    conflict_type=ConflictType.COVERAGE_GAP,
                    status=ConflictStatus.OPEN,
                    process_id=gap["process_id"],
                    conflict_date=gap["work_date"],
                    description="Staffing coverage requirement not met",
                    details={
                        "required_employees": gap["required_employees"],
                        "unfilled_employees": gap["unfilled_employees"],
                        "starts_at": gap["starts_at"].isoformat(),
                        "ends_at": gap["ends_at"].isoformat(),
                    },
                )
            )

        db.commit()
        db.refresh(generation)

        return {
            "message": "Roster generation saved successfully",
            "roster_id": str(roster.roster_id),
            "generation_id": str(generation.generation_id),
            "generation_number": generation.generation_number,
            "solver_status": generation.solver_status.value,
            "total_assignments": len(result.assignments),
            "total_conflicts": len(result.unmet_coverage),
        }

    except Exception:
        db.rollback()
        raise
    
    
def generate_and_persist_roster(
    db: Session,
    roster: Roster,
    time_limit_seconds: int = 30,
):
    if roster.status != RosterStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Only draft rosters can be generated",
        )

    if roster.period_status != RosterPeriodStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail="Archived roster periods cannot be generated",
        )

    try:
        employees, options = build_candidate_options(db, roster)

        employee_limits = build_employee_limits(
            db, employees, roster
        )

        staffing_slots = build_staffing_slots(db, roster)

        unavailable_periods = build_unavailable_periods(
            db, employees, roster
        )

        result = solve_roster(
            options=options,
            staffing_slots=staffing_slots,
            employee_limits=employee_limits,
            unavailable_periods=unavailable_periods,
            time_limit_seconds=time_limit_seconds,
            relax_coverage=True,
        )

        return persist_roster_generation(
            db=db,
            roster=roster,
            result=result,
            time_limit_seconds=time_limit_seconds,
        )

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))