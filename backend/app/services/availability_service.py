
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.availability import (
    AvailabilityRestriction,
    PublicHoliday,
)
from app.models.employee import Employee
from app.models.organization import Brand
from app.models.enums import (
    EmployeeStatus,
    AvailabilityType,
    HolidayScope,
)


# =====================================================
# COMMON VALIDATIONS
# =====================================================

def validate_employee(db: Session, employee_id: UUID):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id,
        Employee.status == EmployeeStatus.ACTIVE
    ).first()

    if not employee:
        raise ValueError("Employee not found or inactive")

    return employee


def validate_availability(
    restriction_type,
    start_time,
    end_time
):
    if restriction_type == AvailabilityType.FULL_DAY:
        if start_time is not None or end_time is not None:
            raise ValueError(
                "FULL_DAY restrictions must not contain start_time or end_time"
            )

    elif restriction_type == AvailabilityType.TIME_SLOT:
        if start_time is None or end_time is None:
            raise ValueError(
                "TIME_SLOT restrictions require both start_time and end_time"
            )

        if end_time <= start_time:
            raise ValueError(
                "End time must be later than start time"
            )


def validate_holiday_scope(db: Session, scope, brand_id):
    if scope == HolidayScope.ORGANIZATION:
        if brand_id is not None:
            raise ValueError(
                "Organization-wide holidays must not have a brand_id"
            )

    elif scope == HolidayScope.BRAND:
        if brand_id is None:
            raise ValueError(
                "Brand-specific holidays require a brand_id"
            )

        brand = db.query(Brand).filter(
            Brand.brand_id == brand_id,
            Brand.is_active == True
        ).first()

        if not brand:
            raise ValueError("Brand not found or inactive")


# =====================================================
# AVAILABILITY OVERLAP VALIDATION
# =====================================================

def validate_availability_overlap(
    db: Session,
    employee_id,
    restriction_date,
    restriction_type,
    start_time,
    end_time,
    exclude_id=None
):
    query = db.query(AvailabilityRestriction).filter(
        AvailabilityRestriction.employee_id == employee_id,
        AvailabilityRestriction.restriction_date == restriction_date,
        AvailabilityRestriction.is_active == True
    )

    if exclude_id is not None:
        query = query.filter(
            AvailabilityRestriction.restriction_id != exclude_id
        )

    existing_records = query.all()

    for existing in existing_records:

        # A full-day restriction conflicts with every
        # other restriction on the same date.
        if (
            restriction_type == AvailabilityType.FULL_DAY
            or existing.restriction_type == AvailabilityType.FULL_DAY
        ):
            raise ValueError(
                "An active restriction already exists for this employee "
                "on this date"
            )

        # Two time slots overlap when their intervals intersect.
        if (
            start_time < existing.end_time
            and end_time > existing.start_time
        ):
            raise ValueError(
                "This time slot overlaps an existing availability restriction"
            )


# =====================================================
# AVAILABILITY RESTRICTION SERVICES
# =====================================================

def create_availability_restriction(db: Session, data):
    validate_employee(db, data.employee_id)

    validate_availability(
        data.restriction_type,
        data.start_time,
        data.end_time
    )

    if data.is_active:
        validate_availability_overlap(
            db,
            data.employee_id,
            data.restriction_date,
            data.restriction_type,
            data.start_time,
            data.end_time
        )

    restriction = AvailabilityRestriction(
        **data.model_dump()
    )

    db.add(restriction)
    db.commit()
    db.refresh(restriction)

    return restriction


def get_all_availability_restrictions(
    db: Session,
    employee_id: UUID | None = None,
    restriction_date=None,
    active_only: bool = False
):
    query = db.query(AvailabilityRestriction)

    if employee_id is not None:
        query = query.filter(
            AvailabilityRestriction.employee_id == employee_id
        )

    if restriction_date is not None:
        query = query.filter(
            AvailabilityRestriction.restriction_date == restriction_date
        )

    if active_only:
        query = query.filter(
            AvailabilityRestriction.is_active == True
        )

    return query.order_by(
        AvailabilityRestriction.restriction_date.desc(),
        AvailabilityRestriction.created_at.desc()
    ).all()


def get_availability_restriction_by_id(
    db: Session,
    restriction_id: UUID
):
    return db.query(AvailabilityRestriction).filter(
        AvailabilityRestriction.restriction_id == restriction_id
    ).first()


def update_availability_restriction(
    db: Session,
    restriction: AvailabilityRestriction,
    data
):
    update_data = data.model_dump(exclude_unset=True)

    restriction_type = update_data.get(
        "restriction_type", restriction.restriction_type
    )

    restriction_date = update_data.get(
        "restriction_date", restriction.restriction_date
    )

    start_time = update_data.get(
        "start_time", restriction.start_time
    )

    end_time = update_data.get(
        "end_time", restriction.end_time
    )

    is_active = update_data.get(
        "is_active", restriction.is_active
    )

    validate_availability(
        restriction_type,
        start_time,
        end_time
    )

    if is_active:
        validate_availability_overlap(
            db,
            restriction.employee_id,
            restriction_date,
            restriction_type,
            start_time,
            end_time,
            exclude_id=restriction.restriction_id
        )

    for key, value in update_data.items():
        setattr(restriction, key, value)

    db.commit()
    db.refresh(restriction)

    return restriction


def deactivate_availability_restriction(
    db: Session,
    restriction: AvailabilityRestriction
):
    restriction.is_active = False

    db.commit()
    db.refresh(restriction)

    return restriction


# =====================================================
# PUBLIC HOLIDAY DUPLICATE VALIDATION
# =====================================================

def validate_holiday_duplicate(
    db: Session,
    holiday_date,
    scope,
    brand_id,
    exclude_id=None
):
    query = db.query(PublicHoliday).filter(
        PublicHoliday.holiday_date == holiday_date,
        PublicHoliday.scope == scope,
        PublicHoliday.is_active == True
    )

    if brand_id is None:
        query = query.filter(PublicHoliday.brand_id.is_(None))
    else:
        query = query.filter(
            PublicHoliday.brand_id == brand_id
        )

    if exclude_id is not None:
        query = query.filter(
            PublicHoliday.holiday_id != exclude_id
        )

    if query.first():
        raise ValueError(
            "An active holiday already exists for this scope and date"
        )


# =====================================================
# PUBLIC HOLIDAY SERVICES
# =====================================================

def create_public_holiday(db: Session, data):
    validate_holiday_scope(
        db,
        data.scope,
        data.brand_id
    )

    if data.is_active:
        validate_holiday_duplicate(
            db,
            data.holiday_date,
            data.scope,
            data.brand_id
        )

    holiday = PublicHoliday(**data.model_dump())

    db.add(holiday)
    db.commit()
    db.refresh(holiday)

    return holiday


def get_all_public_holidays(
    db: Session,
    holiday_date=None,
    scope=None,
    brand_id: UUID | None = None,
    active_only: bool = False
):
    query = db.query(PublicHoliday)

    if holiday_date is not None:
        query = query.filter(
            PublicHoliday.holiday_date == holiday_date
        )

    if scope is not None:
        query = query.filter(
            PublicHoliday.scope == scope
        )

    if brand_id is not None:
        query = query.filter(
            PublicHoliday.brand_id == brand_id
        )

    if active_only:
        query = query.filter(
            PublicHoliday.is_active == True
        )

    return query.order_by(
        PublicHoliday.holiday_date
    ).all()


def get_public_holiday_by_id(
    db: Session,
    holiday_id: UUID
):
    return db.query(PublicHoliday).filter(
        PublicHoliday.holiday_id == holiday_id
    ).first()


def update_public_holiday(
    db: Session,
    holiday: PublicHoliday,
    data
):
    update_data = data.model_dump(exclude_unset=True)

    scope = update_data.get("scope", holiday.scope)
    brand_id = update_data.get("brand_id", holiday.brand_id)
    holiday_date = update_data.get(
        "holiday_date", holiday.holiday_date
    )
    is_active = update_data.get(
        "is_active", holiday.is_active
    )

    validate_holiday_scope(db, scope, brand_id)

    if is_active:
        validate_holiday_duplicate(
            db,
            holiday_date,
            scope,
            brand_id,
            exclude_id=holiday.holiday_id
        )

    for key, value in update_data.items():
        setattr(holiday, key, value)

    db.commit()
    db.refresh(holiday)

    return holiday


def deactivate_public_holiday(
    db: Session,
    holiday: PublicHoliday
):
    holiday.is_active = False

    db.commit()
    db.refresh(holiday)

    return holiday
