
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
from app.schemas.organization_schema import (
    PodCreate,
    PodUpdate,
    PodResponse
)


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

@router.post(
    "/pods",
    response_model=PodResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_operations_manager)]
)
def create_pod(
    pod_data: PodCreate,
    db: Session = Depends(get_db)
):
    try:
        return organization_service.create_pod(db, pod_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Pod name already exists"
        )


@router.get(
    "/pods",
    response_model=list[PodResponse],
    dependencies=[Depends(require_operations_manager)]
)
def get_all_pods(db: Session = Depends(get_db)):
    return organization_service.get_all_pods(db)


@router.get(
    "/pods/{pod_id}",
    response_model=PodResponse,
    dependencies=[Depends(require_operations_manager)]
)
def get_pod(pod_id: UUID, db: Session = Depends(get_db)):
    pod = organization_service.get_pod_by_id(db, pod_id)

    if not pod:
        raise HTTPException(
            status_code=404,
            detail="Pod not found"
        )

    return pod

from app.services.organization_service import validate_pod_lead
@router.patch(
    "/pods/{pod_id}",
    response_model=PodResponse,
    dependencies=[Depends(require_operations_manager)]
)
def update_pod(
    pod_id: UUID,
    pod_data: PodUpdate,
    db: Session = Depends(get_db)
):
    pod = organization_service.get_pod_by_id(db, pod_id)

    if not pod:
        raise HTTPException(
            status_code=404,
            detail="Pod not found"
        )

    update_data = pod_data.model_dump(exclude_unset=True)

    if "pod_lead_id" in update_data and update_data["pod_lead_id"]:
        employee = validate_pod_lead(
            db, update_data["pod_lead_id"]
        )

        if employee.pod_id != pod.pod_id:
            raise HTTPException(
                status_code=400,
                detail="Pod Lead must belong to the same pod"
            )

    for key, value in update_data.items():
        setattr(pod, key, value)

    db.commit()
    db.refresh(pod)

    return pod


@router.delete(
    "/pods/{pod_id}",
    response_model=PodResponse,
    dependencies=[Depends(require_operations_manager)]
)
def delete_pod(pod_id: UUID, db: Session = Depends(get_db)):
    pod = organization_service.get_pod_by_id(db, pod_id)

    if not pod:
        raise HTTPException(
            status_code=404,
            detail="Pod not found"
        )

    return organization_service.delete_pod(db, pod)