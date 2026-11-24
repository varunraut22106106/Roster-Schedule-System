
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.roster import Roster
from app.models.enums import RosterStatus, RosterPeriodStatus


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
