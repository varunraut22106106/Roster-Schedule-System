
from uuid import UUID
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import or_ , and_

from app.models.policies import (
    Shift,
    ProcessOperatingDay,
    StaffingRequirement,
    WeeklyOffPolicy,
    WorkloadPolicy,
)
from app.models.organization import Pod, Process, Brand
from app.models.enums import StaffingRuleScope


# ---------------- COMMON VALIDATIONS ----------------

def validate_date_range(start_date, end_date):
    if end_date is not None and end_date < start_date:
        raise ValueError("Effective until cannot be before effective from")


def validate_process(db: Session, process_id: UUID):
    process = (
        db.query(Process)
        .join(Brand, Process.brand_id == Brand.brand_id)
        .filter(
            Process.process_id == process_id,
            Process.is_active == True,
            Brand.is_active == True
        )
        .first()
    )

    if not process:
        raise ValueError("Process not found or inactive")

    return process


def validate_shift(db: Session, shift_id: UUID | None):
    if shift_id is None:
        return None

    shift = db.query(Shift).filter(
        Shift.shift_id == shift_id,
        Shift.is_active == True
    ).first()

    if not shift:
        raise ValueError("Shift not found or inactive")

    return shift


def validate_staffing_scope(scope, weekday, effective_date):
    if scope == StaffingRuleScope.DEFAULT:
        if weekday is not None or effective_date is not None:
            raise ValueError(
                "DEFAULT scope must not contain weekday or effective_date"
            )

    elif scope == StaffingRuleScope.WEEKDAY:
        if weekday is None:
            raise ValueError("WEEKDAY scope requires a weekday")

        if effective_date is not None:
            raise ValueError(
                "WEEKDAY scope must not contain effective_date"
            )

    elif scope == StaffingRuleScope.DATE:
        if effective_date is None:
            raise ValueError("DATE scope requires an effective_date")

        if weekday is not None:
            raise ValueError("DATE scope must not contain weekday")



def validate_staffing_time_slot(start_time, end_time):
    if (start_time is None) != (end_time is None):
        raise ValueError(
            "Both start_time and end_time must be provided together"
        )

    if start_time is not None and end_time <= start_time:
        raise ValueError("Staffing slot end_time must be after start_time")


def check_staffing_requirement_conflict(
    db: Session,
    process_id,
    shift_id,
    scope,
    weekday,
    effective_date,
    start_time,
    end_time,
    exclude_id=None
):
    query = db.query(StaffingRequirement).filter(
        StaffingRequirement.process_id == process_id,
        StaffingRequirement.shift_id == shift_id,
        StaffingRequirement.scope == scope,
        StaffingRequirement.weekday == weekday,
        StaffingRequirement.effective_date == effective_date,
        StaffingRequirement.is_active == True
    )

    if exclude_id:
        query = query.filter(
            StaffingRequirement.requirement_id != exclude_id
        )

    # A full-shift requirement cannot coexist with another
    # requirement for the same process, shift and scope.
    if start_time is None:
        conflict = query.first()
    else:
        query = query.filter(
            or_(
                and_(
                    StaffingRequirement.start_time.is_(None),
                    StaffingRequirement.end_time.is_(None)
                ),
                and_(
                    StaffingRequirement.start_time < end_time,
                    StaffingRequirement.end_time > start_time
                )
            )
        )
        conflict = query.first()

    if conflict:
        raise ValueError(
            "An active staffing requirement already exists "
            "for an overlapping time slot in this process and scope"
        )



def check_policy_overlap(
    db: Session,
    model,
    start_date,
    end_date,
    exclude_id=None,
    pod_id=None,
    check_pod=False
):
    query = db.query(model).filter(
        model.is_active == True,
        model.effective_from <= (
            end_date if end_date is not None else date.max
        ),
        or_(
            model.effective_until.is_(None),
            model.effective_until >= start_date
        )
    )

    if check_pod:
        query = query.filter(model.pod_id == pod_id)

    if exclude_id:
        query = query.filter(model.policy_id != exclude_id)

    if query.first():
        raise ValueError(
            "An active policy already exists with an overlapping "
            "effective date range"
        )


# ---------------- SHIFT SERVICES ----------------

def create_shift(db: Session, data):
    shift = Shift(**data.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def get_all_shifts(db: Session):
    return db.query(Shift).order_by(Shift.shift_name).all()


def get_shift_by_id(db: Session, shift_id: UUID):
    return db.query(Shift).filter(
        Shift.shift_id == shift_id
    ).first()


def update_shift(db: Session, shift: Shift, data):
    update_data = data.model_dump(exclude_unset=True)

    start_time = update_data.get("start_time", shift.start_time)
    end_time = update_data.get("end_time", shift.end_time)

    if start_time == end_time:
        raise ValueError("Shift start time and end time cannot be identical")

    for key, value in update_data.items():
        setattr(shift, key, value)

    db.commit()
    db.refresh(shift)
    return shift


def deactivate_shift(db: Session, shift: Shift):
    shift.is_active = False
    db.commit()
    db.refresh(shift)
    return shift


# ---------------- PROCESS OPERATING DAY SERVICES ----------------

def create_process_operating_day(db: Session, data):
    validate_process(db, data.process_id)

    existing = db.query(ProcessOperatingDay).filter(
        ProcessOperatingDay.process_id == data.process_id,
        ProcessOperatingDay.weekday == data.weekday
    ).first()

    if existing:
        raise ValueError(
            "Operating day already exists for this process and weekday"
        )

    operating_day = ProcessOperatingDay(**data.model_dump())
    db.add(operating_day)
    db.commit()
    db.refresh(operating_day)
    return operating_day


def get_all_process_operating_days(
    db: Session,
    process_id: UUID | None = None
):
    query = db.query(ProcessOperatingDay)

    if process_id:
        query = query.filter(
            ProcessOperatingDay.process_id == process_id
        )

    return query.order_by(
        ProcessOperatingDay.process_id,
        ProcessOperatingDay.weekday
    ).all()


def get_process_operating_day_by_id(
    db: Session,
    operating_day_id: UUID
):
    return db.query(ProcessOperatingDay).filter(
        ProcessOperatingDay.operating_day_id == operating_day_id
    ).first()


def update_process_operating_day(
    db: Session,
    operating_day: ProcessOperatingDay,
    data
):
    update_data = data.model_dump(exclude_unset=True)

    process_id = operating_day.process_id
    weekday = update_data.get("weekday", operating_day.weekday)

    existing = db.query(ProcessOperatingDay).filter(
        ProcessOperatingDay.process_id == process_id,
        ProcessOperatingDay.weekday == weekday,
        ProcessOperatingDay.operating_day_id != operating_day.operating_day_id
    ).first()

    if existing:
        raise ValueError(
            "Operating day already exists for this process and weekday"
        )

    for key, value in update_data.items():
        setattr(operating_day, key, value)

    db.commit()
    db.refresh(operating_day)
    return operating_day


def delete_process_operating_day(
    db: Session,
    operating_day: ProcessOperatingDay
):
    db.delete(operating_day)
    db.commit()
    return {"message": "Process operating day deleted successfully"}


# ---------------- STAFFING REQUIREMENT SERVICES ----------------


def create_staffing_requirement(db: Session, data):
    validate_process(db, data.process_id)
    validate_shift(db, data.shift_id)

    validate_staffing_scope(
        data.scope,
        data.weekday,
        data.effective_date
    )

    validate_staffing_time_slot(
        data.start_time,
        data.end_time
    )

    if data.is_active:
        check_staffing_requirement_conflict(
            db,
            data.process_id,
            data.shift_id,
            data.scope,
            data.weekday,
            data.effective_date,
            data.start_time,
            data.end_time
        )

    requirement = StaffingRequirement(**data.model_dump())

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement



def get_all_staffing_requirements(
    db: Session,
    process_id: UUID | None = None
):
    query = db.query(StaffingRequirement)

    if process_id:
        query = query.filter(
            StaffingRequirement.process_id == process_id
        )

    return query.order_by(
        StaffingRequirement.created_at.desc()
    ).all()


def get_staffing_requirement_by_id(
    db: Session,
    requirement_id: UUID
):
    return db.query(StaffingRequirement).filter(
        StaffingRequirement.requirement_id == requirement_id
    ).first()



def update_staffing_requirement(
    db: Session,
    requirement: StaffingRequirement,
    data
):
    update_data = data.model_dump(exclude_unset=True)

    process_id = update_data.get(
        "process_id", requirement.process_id
    )
    shift_id = update_data.get(
        "shift_id", requirement.shift_id
    )
    scope = update_data.get("scope", requirement.scope)
    weekday = update_data.get("weekday", requirement.weekday)
    effective_date = update_data.get(
        "effective_date", requirement.effective_date
    )
    start_time = update_data.get(
        "start_time", requirement.start_time
    )
    end_time = update_data.get(
        "end_time", requirement.end_time
    )
    is_active = update_data.get(
        "is_active", requirement.is_active
    )

    validate_process(db, process_id)
    validate_shift(db, shift_id)

    validate_staffing_scope(scope, weekday, effective_date)
    validate_staffing_time_slot(start_time, end_time)

    if is_active:
        check_staffing_requirement_conflict(
            db,
            process_id,
            shift_id,
            scope,
            weekday,
            effective_date,
            start_time,
            end_time,
            exclude_id=requirement.requirement_id
        )

    for key, value in update_data.items():
        setattr(requirement, key, value)

    db.commit()
    db.refresh(requirement)

    return requirement



def deactivate_staffing_requirement(
    db: Session,
    requirement: StaffingRequirement
):
    requirement.is_active = False
    db.commit()
    db.refresh(requirement)
    return requirement


# ---------------- WEEKLY OFF POLICY SERVICES ----------------

def create_weekly_off_policy(db: Session, data):
    validate_date_range(data.effective_from, data.effective_until)

    if data.pod_id is not None:
        pod = db.query(Pod).filter(
            Pod.pod_id == data.pod_id,
            Pod.is_active == True
        ).first()

        if not pod:
            raise ValueError("Pod not found or inactive")

    if data.is_active:
        check_policy_overlap(
            db,
            WeeklyOffPolicy,
            data.effective_from,
            data.effective_until,
            pod_id=data.pod_id,
            check_pod=True
        )

    policy = WeeklyOffPolicy(**data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_all_weekly_off_policies(db: Session):
    return db.query(WeeklyOffPolicy).order_by(
        WeeklyOffPolicy.effective_from.desc()
    ).all()


def get_weekly_off_policy_by_id(db: Session, policy_id: UUID):
    return db.query(WeeklyOffPolicy).filter(
        WeeklyOffPolicy.policy_id == policy_id
    ).first()


def update_weekly_off_policy(
    db: Session,
    policy: WeeklyOffPolicy,
    data
):
    update_data = data.model_dump(exclude_unset=True)

    effective_from = update_data.get(
        "effective_from", policy.effective_from
    )
    effective_until = update_data.get(
        "effective_until", policy.effective_until
    )
    pod_id = update_data.get("pod_id", policy.pod_id)
    is_active = update_data.get("is_active", policy.is_active)

    validate_date_range(effective_from, effective_until)

    if pod_id is not None:
        pod = db.query(Pod).filter(
            Pod.pod_id == pod_id,
            Pod.is_active == True
        ).first()

        if not pod:
            raise ValueError("Pod not found or inactive")

    if is_active:
        check_policy_overlap(
            db,
            WeeklyOffPolicy,
            effective_from,
            effective_until,
            exclude_id=policy.policy_id,
            pod_id=pod_id,
            check_pod=True
        )

    for key, value in update_data.items():
        setattr(policy, key, value)

    db.commit()
    db.refresh(policy)
    return policy


def deactivate_weekly_off_policy(db: Session, policy: WeeklyOffPolicy):
    policy.is_active = False
    db.commit()
    db.refresh(policy)
    return policy


# ---------------- WORKLOAD POLICY SERVICES ----------------

def create_workload_policy(db: Session, data):
    validate_date_range(data.effective_from, data.effective_until)

    if data.is_active:
        check_policy_overlap(
            db,
            WorkloadPolicy,
            data.effective_from,
            data.effective_until
        )

    policy = WorkloadPolicy(**data.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def get_all_workload_policies(db: Session):
    return db.query(WorkloadPolicy).order_by(
        WorkloadPolicy.effective_from.desc()
    ).all()


def get_workload_policy_by_id(db: Session, policy_id: UUID):
    return db.query(WorkloadPolicy).filter(
        WorkloadPolicy.policy_id == policy_id
    ).first()


def update_workload_policy(
    db: Session,
    policy: WorkloadPolicy,
    data
):
    update_data = data.model_dump(exclude_unset=True)

    effective_from = update_data.get(
        "effective_from", policy.effective_from
    )
    effective_until = update_data.get(
        "effective_until", policy.effective_until
    )
    is_active = update_data.get("is_active", policy.is_active)

    validate_date_range(effective_from, effective_until)

    if is_active:
        check_policy_overlap(
            db,
            WorkloadPolicy,
            effective_from,
            effective_until,
            exclude_id=policy.policy_id
        )

    for key, value in update_data.items():
        setattr(policy, key, value)

    db.commit()
    db.refresh(policy)
    return policy


def deactivate_workload_policy(db: Session, policy: WorkloadPolicy):
    policy.is_active = False
    db.commit()
    db.refresh(policy)
    return policy
