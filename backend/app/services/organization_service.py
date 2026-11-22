
from sqlalchemy.orm import Session

from app.models.organization import Brand
from app.schemas.organization_schema import BrandCreate, BrandUpdate
from app.models.organization import Process, Brand
from app.schemas.organization_schema import ProcessCreate, ProcessUpdate


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


def create_process(db: Session, process_data: ProcessCreate):
    brand = db.query(Brand).filter(
        Brand.brand_id == process_data.brand_id,
        Brand.is_active == True
    ).first()

    if not brand:
        raise ValueError("Brand not found or inactive")

    process = Process(**process_data.model_dump())

    db.add(process)
    db.commit()
    db.refresh(process)

    return process


def get_all_processes(db: Session):
    return db.query(Process).order_by(
        Process.created_at.desc()
    ).all()


def get_process_by_id(db: Session, process_id):
    return db.query(Process).filter(
        Process.process_id == process_id
    ).first()


def update_process(db: Session, process, process_data: ProcessUpdate):
    update_data = process_data.model_dump(exclude_unset=True)

    if "brand_id" in update_data:
        brand = db.query(Brand).filter(
            Brand.brand_id == update_data["brand_id"],
            Brand.is_active == True
        ).first()

        if not brand:
            raise ValueError("Brand not found or inactive")

    for key, value in update_data.items():
        setattr(process, key, value)

    db.commit()
    db.refresh(process)

    return process


def delete_process(db: Session, process):
    process.is_active = False

    db.commit()
    db.refresh(process)

    return process
