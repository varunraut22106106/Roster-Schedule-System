
from datetime import date

from app.database.session import SessionLocal
from app.models.organization import Pod
from app.models.employee import Employee
from app.models.auth import UserAccount
from app.models.enums import EmployeeStatus, UserRole
from app.core.security import hash_password


db = SessionLocal()

try:
    # 1. Create Pod
    pod = Pod(
        pod_name="Testing Pod",
        is_active=True
    )

    db.add(pod)
    db.flush()

    # 2. Create Employee
    employee = Employee(
        employee_code="EMP001",
        full_name="Test Employee",
        email="test@example.com",
        pod_id=pod.pod_id,
        status=EmployeeStatus.ACTIVE,
        joined_at=date.today()
    )

    db.add(employee)
    db.flush()

    # 3. Create User Account
    user = UserAccount(
        employee_id=employee.employee_id,
        password_hash=hash_password("Test@12345"),
        role=UserRole.OPERATIONS_MANAGER,
        is_active=True
    )

    db.add(user)
    db.commit()

    print("Test account created successfully!")
    print("Email: test@example.com")
    print("Password: Test@12345")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
