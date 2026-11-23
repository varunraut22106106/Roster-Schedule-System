
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager

from app.schemas.policies_schema import (
    ShiftCreate, ShiftUpdate, ShiftResponse,
    ProcessOperatingDayCreate, ProcessOperatingDayUpdate,
    ProcessOperatingDayResponse,
    StaffingRequirementCreate, StaffingRequirementUpdate,
    StaffingRequirementResponse,
    WeeklyOffPolicyCreate, WeeklyOffPolicyUpdate,
    WeeklyOffPolicyResponse,
    WorkloadPolicyCreate, WorkloadPolicyUpdate,
    WorkloadPolicyResponse
)

from app.services import policy_service as service

from app.models.policies import (
    Shift, ProcessOperatingDay, StaffingRequirement,
    WeeklyOffPolicy, WorkloadPolicy
)


router = APIRouter(
    prefix="/policies",
    tags=["Policies and Shift Management"],
    dependencies=[Depends(require_operations_manager)]
)


def get_or_404(db, model, field, value, message):
    record = db.query(model).filter(field == value).first()

    if not record:
        raise HTTPException(status_code=404, detail=message)

    return record


def handle_value_error(error):
    raise HTTPException(status_code=400, detail=str(error))


def handle_integrity_error(db, message):
    db.rollback()
    raise HTTPException(status_code=409, detail=message)


# =====================================================
# SHIFT ROUTES
# =====================================================

@router.post(
    "/shifts",
    response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED
)
def create_shift(data: ShiftCreate, db: Session = Depends(get_db)):
    try:
        if data.start_time == data.end_time:
            raise ValueError(
                "Shift start time and end time cannot be identical"
            )
        return service.create_shift(db, data)
    except IntegrityError:
        handle_integrity_error(db, "Shift name already exists")
    except ValueError as e:
        handle_value_error(e)


@router.get("/shifts", response_model=list[ShiftResponse])
def get_all_shifts(db: Session = Depends(get_db)):
    return service.get_all_shifts(db)


@router.get("/shifts/{shift_id}", response_model=ShiftResponse)
def get_shift(shift_id: UUID, db: Session = Depends(get_db)):
    shift = service.get_shift_by_id(db, shift_id)

    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    return shift


@router.patch("/shifts/{shift_id}", response_model=ShiftResponse)
def update_shift(
    shift_id: UUID,
    data: ShiftUpdate,
    db: Session = Depends(get_db)
):
    shift = service.get_shift_by_id(db, shift_id)

    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    try:
        return service.update_shift(db, shift, data)
    except IntegrityError:
        handle_integrity_error(db, "Shift name already exists")
    except ValueError as e:
        handle_value_error(e)


@router.delete("/shifts/{shift_id}", response_model=ShiftResponse)
def deactivate_shift(
    shift_id: UUID,
    db: Session = Depends(get_db)
):
    shift = service.get_shift_by_id(db, shift_id)

    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")

    return service.deactivate_shift(db, shift)


# =====================================================
# PROCESS OPERATING DAY ROUTES
# =====================================================

@router.post(
    "/operating-days",
    response_model=ProcessOperatingDayResponse,
    status_code=status.HTTP_201_CREATED
)
def create_operating_day(
    data: ProcessOperatingDayCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_process_operating_day(db, data)
    except IntegrityError:
        handle_integrity_error(
            db, "Operating day already exists for this process"
        )
    except ValueError as e:
        handle_value_error(e)


@router.get(
    "/operating-days",
    response_model=list[ProcessOperatingDayResponse]
)
def get_all_operating_days(
    process_id: UUID | None = None,
    db: Session = Depends(get_db)
):
    return service.get_all_process_operating_days(db, process_id)


@router.get(
    "/operating-days/{operating_day_id}",
    response_model=ProcessOperatingDayResponse
)
def get_operating_day(
    operating_day_id: UUID,
    db: Session = Depends(get_db)
):
    record = service.get_process_operating_day_by_id(
        db, operating_day_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Process operating day not found"
        )

    return record


@router.patch(
    "/operating-days/{operating_day_id}",
    response_model=ProcessOperatingDayResponse
)
def update_operating_day(
    operating_day_id: UUID,
    data: ProcessOperatingDayUpdate,
    db: Session = Depends(get_db)
):
    record = service.get_process_operating_day_by_id(
        db, operating_day_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Process operating day not found"
        )

    try:
        return service.update_process_operating_day(db, record, data)
    except IntegrityError:
        handle_integrity_error(
            db, "Operating day already exists for this process"
        )
    except ValueError as e:
        handle_value_error(e)


@router.delete("/operating-days/{operating_day_id}")
def delete_operating_day(
    operating_day_id: UUID,
    db: Session = Depends(get_db)
):
    record = service.get_process_operating_day_by_id(
        db, operating_day_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Process operating day not found"
        )

    return service.delete_process_operating_day(db, record)


# =====================================================
# STAFFING REQUIREMENT ROUTES
# =====================================================

@router.post(
    "/staffing-requirements",
    response_model=StaffingRequirementResponse,
    status_code=status.HTTP_201_CREATED
)
def create_staffing_requirement(
    data: StaffingRequirementCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_staffing_requirement(db, data)
    except IntegrityError:
        handle_integrity_error(
            db, "Duplicate staffing requirement"
        )
    except ValueError as e:
        handle_value_error(e)


@router.get(
    "/staffing-requirements",
    response_model=list[StaffingRequirementResponse]
)
def get_all_staffing_requirements(
    process_id: UUID | None = None,
    db: Session = Depends(get_db)
):
    return service.get_all_staffing_requirements(db, process_id)


@router.get(
    "/staffing-requirements/{requirement_id}",
    response_model=StaffingRequirementResponse
)
def get_staffing_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db)
):
    record = service.get_staffing_requirement_by_id(
        db, requirement_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Staffing requirement not found"
        )

    return record


@router.patch(
    "/staffing-requirements/{requirement_id}",
    response_model=StaffingRequirementResponse
)
def update_staffing_requirement(
    requirement_id: UUID,
    data: StaffingRequirementUpdate,
    db: Session = Depends(get_db)
):
    record = service.get_staffing_requirement_by_id(
        db, requirement_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Staffing requirement not found"
        )

    try:
        return service.update_staffing_requirement(db, record, data)
    except IntegrityError:
        handle_integrity_error(
            db, "Duplicate staffing requirement"
        )
    except ValueError as e:
        handle_value_error(e)


@router.delete(
    "/staffing-requirements/{requirement_id}",
    response_model=StaffingRequirementResponse
)
def deactivate_staffing_requirement(
    requirement_id: UUID,
    db: Session = Depends(get_db)
):
    record = service.get_staffing_requirement_by_id(
        db, requirement_id
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Staffing requirement not found"
        )

    return service.deactivate_staffing_requirement(db, record)


# =====================================================
# WEEKLY OFF POLICY ROUTES
# =====================================================

@router.post(
    "/weekly-off",
    response_model=WeeklyOffPolicyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_weekly_off_policy(
    data: WeeklyOffPolicyCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_weekly_off_policy(db, data)
    except IntegrityError:
        handle_integrity_error(db, "Unable to create weekly-off policy")
    except ValueError as e:
        handle_value_error(e)


@router.get("/weekly-off", response_model=list[WeeklyOffPolicyResponse])
def get_all_weekly_off_policies(db: Session = Depends(get_db)):
    return service.get_all_weekly_off_policies(db)


@router.get(
    "/weekly-off/{policy_id}",
    response_model=WeeklyOffPolicyResponse
)
def get_weekly_off_policy(
    policy_id: UUID,
    db: Session = Depends(get_db)
):
    policy = service.get_weekly_off_policy_by_id(db, policy_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Weekly-off policy not found"
        )

    return policy


@router.patch(
    "/weekly-off/{policy_id}",
    response_model=WeeklyOffPolicyResponse
)
def update_weekly_off_policy(
    policy_id: UUID,
    data: WeeklyOffPolicyUpdate,
    db: Session = Depends(get_db)
):
    policy = service.get_weekly_off_policy_by_id(db, policy_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Weekly-off policy not found"
        )

    try:
        return service.update_weekly_off_policy(db, policy, data)
    except IntegrityError:
        handle_integrity_error(db, "Unable to update weekly-off policy")
    except ValueError as e:
        handle_value_error(e)


@router.delete(
    "/weekly-off/{policy_id}",
    response_model=WeeklyOffPolicyResponse
)
def deactivate_weekly_off_policy(
    policy_id: UUID,
    db: Session = Depends(get_db)
):
    policy = service.get_weekly_off_policy_by_id(db, policy_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Weekly-off policy not found"
        )

    return service.deactivate_weekly_off_policy(db, policy)


# =====================================================
# WORKLOAD POLICY ROUTES
# =====================================================

@router.post(
    "/workload",
    response_model=WorkloadPolicyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_workload_policy(
    data: WorkloadPolicyCreate,
    db: Session = Depends(get_db)
):
    try:
        return service.create_workload_policy(db, data)
    except IntegrityError:
        handle_integrity_error(db, "Unable to create workload policy")
    except ValueError as e:
        handle_value_error(e)


@router.get("/workload", response_model=list[WorkloadPolicyResponse])
def get_all_workload_policies(db: Session = Depends(get_db)):
    return service.get_all_workload_policies(db)


@router.get(
    "/workload/{policy_id}",
    response_model=WorkloadPolicyResponse
)
def get_workload_policy(
    policy_id: UUID,
    db: Session = Depends(get_db)
):
    policy = service.get_workload_policy_by_id(db, policy_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Workload policy not found"
        )

    return policy


@router.patch(
    "/workload/{policy_id}",
    response_model=WorkloadPolicyResponse
)
def update_workload_policy(
    policy_id: UUID,
    data: WorkloadPolicyUpdate,
    db: Session = Depends(get_db)
):
    policy = service.get_workload_policy_by_id(db, policy_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Workload policy not found"
        )

    try:
        return service.update_workload_policy(db, policy, data)
    except IntegrityError:
        handle_integrity_error(db, "Unable to update workload policy")
    except ValueError as e:
        handle_value_error(e)


@router.delete(
    "/workload/{policy_id}",
    response_model=WorkloadPolicyResponse
)
def deactivate_workload_policy(
    policy_id: UUID,
    db: Session = Depends(get_db)
):
    policy = service.get_workload_policy_by_id(db, policy_id)

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Workload policy not found"
        )

    return service.deactivate_workload_policy(db, policy)
