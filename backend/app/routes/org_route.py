
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.permissions import require_operations_manager
from app.schemas.organization_schema import (
    BrandCreate,
    BrandUpdate,
    BrandResponse
)
from app.services import organization_service as organization_service


router = APIRouter(
    prefix="/organization",
    tags=["Organization"]
)


@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operations_manager)]
)
def create_brand(
    brand_data: BrandCreate,
    db: Session = Depends(get_db)
):
    try:
        return organization_service.create_brand(db, brand_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Brand name already exists"
        )


@router.get(
    "/brands",
    response_model=list[BrandResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_brands(db: Session = Depends(get_db)):
    return organization_service.get_all_brands(db)


@router.get(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_brand(brand_id: UUID, db: Session = Depends(get_db)):
    brand = organization_service.get_brand_by_id(db, brand_id)

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Brand not found"
        )

    return brand


@router.patch(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    dependencies=[Depends(require_operations_manager)]
)
def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdate,
    db: Session = Depends(get_db)
):
    brand = organization_service.get_brand_by_id(db, brand_id)

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Brand not found"
        )

    try:
        return organization_service.update_brand(
            db, brand, brand_data
        )
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Brand name already exists"
        )


@router.delete(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    dependencies=[Depends(require_operations_manager)]
)
def delete_brand(brand_id: UUID, db: Session = Depends(get_db)):
    brand = organization_service.get_brand_by_id(db, brand_id)

    if not brand:
        raise HTTPException(
            status_code=404,
            detail="Brand not found"
        )

    return organization_service.delete_brand(db, brand)
