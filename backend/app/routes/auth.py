
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.auth import UserAccount
from app.models.employee import Employee

from app.schemas.auth_schema import LoginRequest, TokenResponse
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    # Find employee using email
    employee = db.query(Employee).filter(
        Employee.email == credentials.email
    ).first()

    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Find associated user account
    user = db.query(UserAccount).filter(
        UserAccount.employee_id == employee.employee_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Check account status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Verify password
    if not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Generate JWT
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
            "role": user.role.value
        }
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer"
    )
    
# Add this below the login endpoint
@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    return {
        "user_id": str(current_user.user_id),
        "employee_id": str(current_user.employee_id),
        "role": current_user.role.value,
        "is_active": current_user.is_active
    }

from app.core.permissions import (
    require_operations_manager,
    require_pod_lead,
    require_employee
)


@router.get("/test-manager")
def test_manager(
    current_user=Depends(require_operations_manager)
):
    return {"message": "Operations Manager access granted"}


@router.get("/test-pod-lead")
def test_pod_lead(
    current_user=Depends(require_pod_lead)
):
    return {"message": "Pod Lead access granted"}


@router.get("/test-employee")
def test_employee(
    current_user=Depends(require_employee)
):
    return {"message": "Employee access granted"}