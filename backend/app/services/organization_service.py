
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
