
from sqlalchemy.orm import Session

from app.models.organization import Brand
from app.schemas.organization_schema import BrandCreate, BrandUpdate


def create_brand(db: Session, brand_data: BrandCreate):
    brand = Brand(**brand_data.model_dump())

    db.add(brand)
    db.commit()
    db.refresh(brand)

    return brand


def get_all_brands(db: Session):
    return db.query(Brand).order_by(Brand.created_at.desc()).all()


def get_brand_by_id(db: Session, brand_id):
    return db.query(Brand).filter(
        Brand.brand_id == brand_id
    ).first()


def update_brand(db: Session, brand, brand_data: BrandUpdate):
    update_data = brand_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(brand, key, value)

    db.commit()
    db.refresh(brand)

    return brand


def delete_brand(db: Session, brand):
    brand.is_active = False

    db.commit()
    db.refresh(brand)

    return brand


from app.models.employee import Employee
from app.models.enums import EmployeeStatus
from app.models.organization import Pod
from app.schemas.organization_schema import PodCreate, PodUpdate


def create_pod(db: Session, pod_data: PodCreate):
    data = pod_data.model_dump()

    pod_lead_id = data.pop("pod_lead_id", None)

    if pod_lead_id:
        validate_pod_lead(db, pod_lead_id)

    pod = Pod(**data, pod_lead_id=pod_lead_id)

    db.add(pod)
    db.commit()
    db.refresh(pod)

    return pod


def get_all_pods(db: Session):
    return db.query(Pod).order_by(Pod.created_at.desc()).all()


def get_pod_by_id(db: Session, pod_id):
    return db.query(Pod).filter(
        Pod.pod_id == pod_id
    ).first()


def validate_pod_lead(db: Session, employee_id):
    employee = db.query(Employee).filter(
        Employee.employee_id == employee_id,
        Employee.status == EmployeeStatus.ACTIVE
    ).first()

    if not employee:
        raise ValueError("Pod Lead must be an active employee")

    return employee


def update_pod(db: Session, pod, pod_data: PodUpdate):
    update_data = pod_data.model_dump(exclude_unset=True)

    if "pod_lead_id" in update_data and update_data["pod_lead_id"]:
        employee = validate_pod_lead(
            db, update_data["pod_lead_id"]
        )

        target_pod_id = update_data.get("pod_id", pod.pod_id)

        if employee.pod_id != target_pod_id:
            raise ValueError(
                "Pod Lead must belong to the same pod"
            )

    for key, value in update_data.items():
        setattr(pod, key, value)

    db.commit()
    db.refresh(pod)

    return pod


def delete_pod(db: Session, pod):
    pod.is_active = False

    db.commit()
    db.refresh(pod)

    return pod



