
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

from app.schemas.organization_schema import (
    ProcessCreate,
    ProcessUpdate,
    ProcessResponse
)


@router.post(
    "/processes",
    response_model=ProcessResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operations_manager)]
)
def create_process(
    process_data: ProcessCreate,
    db: Session = Depends(get_db)
):
    try:
        return organization_service.create_process(db, process_data)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Process already exists for this brand"
        )


@router.get(
    "/processes",
    response_model=list[ProcessResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_processes(db: Session = Depends(get_db)):
    return organization_service.get_all_processes(db)


@router.get(
    "/processes/{process_id}",
    response_model=ProcessResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_process(
    process_id: UUID,
    db: Session = Depends(get_db)
):
    process = organization_service.get_process_by_id(
        db, process_id
    )

    if not process:
        raise HTTPException(
            status_code=404,
            detail="Process not found"
        )

    return process


@router.patch(
    "/processes/{process_id}",
    response_model=ProcessResponse,
    dependencies=[Depends(require_operations_manager)]
)
def update_process(
    process_id: UUID,
    process_data: ProcessUpdate,
    db: Session = Depends(get_db)
):
    process = organization_service.get_process_by_id(
        db, process_id
    )

    if not process:
        raise HTTPException(
            status_code=404,
            detail="Process not found"
        )

    try:
        return organization_service.update_process(
            db, process, process_data
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Process name already exists for this brand"
        )


@router.delete(
    "/processes/{process_id}",
    response_model=ProcessResponse,
    dependencies=[Depends(require_operations_manager)]
)
def delete_process(
    process_id: UUID,
    db: Session = Depends(get_db)
):
    process = organization_service.get_process_by_id(
        db, process_id
    )

    if not process:
        raise HTTPException(
            status_code=404,
            detail="Process not found"
        )

    return organization_service.delete_process(db, process)

