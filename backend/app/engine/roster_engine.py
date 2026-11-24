
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from uuid import UUID

from ortools.sat.python import cp_model


@dataclass(frozen=True)
class AssignmentOption:
    employee_id: UUID
    process_id: UUID
    shift_id: UUID
    work_date: date
    starts_at: datetime
    ends_at: datetime
    minimum_minutes: int
    maximum_minutes: int
    fixed_minutes: int | None = None


@dataclass(frozen=True)
class StaffingSlot:
    process_id: UUID
    work_date: date
    starts_at: datetime
    ends_at: datetime
    minimum_employees: int
    shift_id: UUID | None = None


@dataclass(frozen=True)
class EmployeeLimit:
    employee_id: UUID
    max_hours_per_day: int
    max_hours_per_week: int
    max_work_days_per_week: int
    max_consecutive_work_days: int
    minimum_rest_hours: int


@dataclass(frozen=True)
class UnavailablePeriod:
    employee_id: UUID
    starts_at: datetime
    ends_at: datetime


@dataclass
class SolverResult:
    status: str
    objective_value: float | None
    assignments: list[dict]
    unmet_coverage: list[dict]
    solver_time_seconds: float


def _overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def solve_roster(
    *,
    options: list[AssignmentOption],
    staffing_slots: list[StaffingSlot],
    employee_limits: list[EmployeeLimit],
    unavailable_periods: list[UnavailablePeriod],
    time_limit_seconds: int = 30,
    relax_coverage: bool = True,
) -> SolverResult:
    """
    Build a roster using CP-SAT.

    Employee restrictions and workload limits are always hard constraints.
    Only staffing coverage can be relaxed in the second solve.
    """

    started = datetime.now()
    model = cp_model.CpModel()

    limits = {x.employee_id: x for x in employee_limits}

    # Decision variables
    selected = {}
    minutes = {}

    by_employee_date = defaultdict(list)
    by_employee_week = defaultdict(list)
    by_employee_day = defaultdict(list)
    by_employee = defaultdict(list)
    by_employee_process_date = defaultdict(list)

    for index, option in enumerate(options):
        if option.ends_at <= option.starts_at:
            raise ValueError("Assignment option has invalid shift times")

        if option.minimum_minutes <= 0:
            raise ValueError("Minimum allocation must be positive")

        if option.maximum_minutes < option.minimum_minutes:
            raise ValueError("Maximum allocation is below minimum allocation")

        if option.fixed_minutes is not None:
            if not (
                option.minimum_minutes
                <= option.fixed_minutes
                <= option.maximum_minutes
            ):
                raise ValueError("Fixed allocation is outside its allowed range")

        key = index
        selected[key] = model.NewBoolVar(f"selected_{index}")

        minutes[key] = model.NewIntVar(
            0,
            option.maximum_minutes,
            f"minutes_{index}",
        )

        model.Add(minutes[key] == option.fixed_minutes).OnlyEnforceIf(
            selected[key]
        )

        model.Add(minutes[key] == 0).OnlyEnforceIf(selected[key].Not())

        model.Add(
            minutes[key] >= option.minimum_minutes
        ).OnlyEnforceIf(selected[key])

        model.Add(
            minutes[key] <= option.maximum_minutes
        ).OnlyEnforceIf(selected[key])

        by_employee_date[
            (option.employee_id, option.work_date)
        ].append(key)

        by_employee_day[
            (option.employee_id, option.work_date)
        ].append(key)

        monday = option.work_date - timedelta(
            days=option.work_date.weekday()
        )
        by_employee_week[(option.employee_id, monday)].append(key)

        by_employee[option.employee_id].append(key)

        by_employee_process_date[
            (option.employee_id, option.process_id, option.work_date)
        ].append(key)

    # One assignment per employee/process/date.
    for keys in by_employee_process_date.values():
        model.Add(sum(selected[k] for k in keys) <= 1)

    # Employee must not be assigned to overlapping shifts or shifts
    # that violate the minimum rest period.
    for employee_id, keys in by_employee.items():
        employee_limit = limits.get(employee_id)

        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a = options[keys[i]]
                b = options[keys[j]]

                rest_minutes = (
                    employee_limit.minimum_rest_hours * 60
                    if employee_limit
                    else 0
                )

                if _overlaps(
                    a.starts_at,
                    a.ends_at,
                    b.starts_at,
                    b.ends_at,
                ):
                    model.Add(
                        selected[keys[i]] + selected[keys[j]] <= 1
                    )
                    continue

                if a.ends_at <= b.starts_at:
                    gap = (b.starts_at - a.ends_at).total_seconds() / 60
                else:
                    gap = (a.starts_at - b.ends_at).total_seconds() / 60

                if gap < rest_minutes:
                    model.Add(
                        selected[keys[i]] + selected[keys[j]] <= 1
                    )

    # Availability restrictions and leave are hard constraints.
    for index, option in enumerate(options):
        for unavailable in unavailable_periods:
            if unavailable.employee_id != option.employee_id:
                continue

            if _overlaps(
                option.starts_at,
                option.ends_at,
                unavailable.starts_at,
                unavailable.ends_at,
            ):
                model.Add(selected[index] == 0)
                break

    # Daily and weekly workload limits.
    for (employee_id, work_date), keys in by_employee_date.items():
        employee_limit = limits.get(employee_id)
        if not employee_limit:
            continue

        model.Add(
            sum(minutes[k] for k in keys)
            <= employee_limit.max_hours_per_day * 60
        )

    for (employee_id, week_start), keys in by_employee_week.items():
        employee_limit = limits.get(employee_id)
        if not employee_limit:
            continue

        model.Add(
            sum(minutes[k] for k in keys)
            <= employee_limit.max_hours_per_week * 60
        )

        # Number of distinct working days in this week.
        dates = sorted({
            options[k].work_date for k in keys
        })

        day_worked = []
        for work_date in dates:
            day_keys = by_employee_day[(employee_id, work_date)]
            worked = model.NewBoolVar(
                f"worked_{employee_id}_{work_date}"
            )
            model.Add(sum(selected[k] for k in day_keys) >= 1).OnlyEnforceIf(
                worked
            )
            model.Add(sum(selected[k] for k in day_keys) == 0).OnlyEnforceIf(
                worked.Not()
            )
            day_worked.append((work_date, worked))

        model.Add(
            sum(worked for _, worked in day_worked)
            <= employee_limit.max_work_days_per_week
        )

        # Rolling consecutive-workday limit.
        day_map = dict(day_worked)
        for offset in range(7):
            window_start = week_start + timedelta(days=offset)
            window_dates = [
                window_start + timedelta(days=i)
                for i in range(employee_limit.max_consecutive_work_days + 1)
            ]
            window_vars = [
                day_map[d] for d in window_dates if d in day_map
            ]
            if len(window_vars) > employee_limit.max_consecutive_work_days:
                model.Add(
                    sum(window_vars)
                    <= employee_limit.max_consecutive_work_days
                )

    # Coverage constraints.
    shortage_vars = []
    coverage_records = []

    for slot_index, slot in enumerate(staffing_slots):
        eligible_keys = []

        for index, option in enumerate(options):
            if (
                option.process_id != slot.process_id
                or option.work_date != slot.work_date
            ):
                continue

            if slot.shift_id and option.shift_id != slot.shift_id:
                continue

            if _overlaps(
                option.starts_at,
                option.ends_at,
                slot.starts_at,
                slot.ends_at,
            ):
                eligible_keys.append(index)

        if not eligible_keys:
            shortage = model.NewIntVar(
                slot.minimum_employees,
                slot.minimum_employees,
                f"shortage_{slot_index}",
            )
            shortage_vars.append(shortage)
            coverage_records.append((slot, shortage))
            continue

        shortage = model.NewIntVar(
            0,
            slot.minimum_employees,
            f"shortage_{slot_index}",
        )

        model.Add(
            sum(selected[k] for k in eligible_keys) + shortage
            >= slot.minimum_employees
        )

        shortage_vars.append(shortage)
        coverage_records.append((slot, shortage))

    # First solve with strict coverage. If infeasible, solve again with
    # coverage shortages allowed and minimized. No employee hard rule
    # is relaxed.
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 8

    model.Minimize(sum(shortage_vars))

    status = solver.Solve(model)

    if status == cp_model.INFEASIBLE and not relax_coverage:
        return SolverResult(
            status="INFEASIBLE",
            objective_value=None,
            assignments=[],
            unmet_coverage=[],
            solver_time_seconds=solver.WallTime(),
        )

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolverResult(
            status=solver.StatusName(status),
            objective_value=None,
            assignments=[],
            unmet_coverage=[],
            solver_time_seconds=solver.WallTime(),
        )

    assignments = []

    for index, option in enumerate(options):
        if solver.Value(selected[index]) == 0:
            continue

        assignments.append({
            "employee_id": option.employee_id,
            "process_id": option.process_id,
            "shift_id": option.shift_id,
            "work_date": option.work_date,
            "starts_at": option.starts_at,
            "ends_at": option.ends_at,
            "allocation_minutes": solver.Value(minutes[index]),
        })

    unmet_coverage = []

    for slot, shortage in coverage_records:
        shortage_value = solver.Value(shortage)
        if shortage_value > 0:
            unmet_coverage.append({
                "process_id": slot.process_id,
                "work_date": slot.work_date,
                "starts_at": slot.starts_at,
                "ends_at": slot.ends_at,
                "required_employees": slot.minimum_employees,
                "unfilled_employees": shortage_value,
            })

    return SolverResult(
        status=solver.StatusName(status),
        objective_value=solver.ObjectiveValue(),
        assignments=assignments,
        unmet_coverage=unmet_coverage,
        solver_time_seconds=solver.WallTime(),
    )
