
from datetime import date, datetime
from uuid import uuid4

from app.engine.roster_engine import (
    AssignmentOption,
    StaffingSlot,
    EmployeeLimit,
    solve_roster,
)

employee_id = uuid4()
process_id = uuid4()
shift_id = uuid4()

work_date = date(2026, 12, 1)

options = [
    AssignmentOption(
        employee_id=employee_id,
        process_id=process_id,
        shift_id=shift_id,
        work_date=work_date,
        starts_at=datetime(2026, 12, 1, 9, 0),
        ends_at=datetime(2026, 12, 1, 17, 0),
        minimum_minutes=480,
        maximum_minutes=480,
        fixed_minutes=480,
    )
]

staffing = [
    StaffingSlot(
        process_id=process_id,
        work_date=work_date,
        starts_at=datetime(2026, 12, 1, 9, 0),
        ends_at=datetime(2026, 12, 1, 17, 0),
        minimum_employees=1,
    )
]

limits = [
    EmployeeLimit(
        employee_id=employee_id,
        max_hours_per_day=9,
        max_hours_per_week=45,
        max_work_days_per_week=5,
        max_consecutive_work_days=5,
        minimum_rest_hours=11,
    )
]

result = solve_roster(
    options=options,
    staffing_slots=staffing,
    employee_limits=limits,
    unavailable_periods=[],
)

print("Status:", result.status)
print("Assignments:", result.assignments)
print("Unmet coverage:", result.unmet_coverage)
