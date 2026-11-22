
from datetime import date

from app.database.session import SessionLocal
from app.models.organization import Pod
from app.models.employee import Employee
from app.models.auth import UserAccount
from app.models.enums import EmployeeStatus, UserRole
from app.core.security import hash_password


db = SessionLocal()

try:
    # Create Testing Pod
    pod = Pod(
        pod_name="RBAC Testing Pod",
        is_active=True
    )

    db.add(pod)
    db.flush()

    # Create Pod Lead Employee
    pod_lead = Employee(
        employee_code="EMP002",
        full_name="Test Pod Lead",
        email="podlead@example.com",
        pod_id=pod.pod_id,
        status=EmployeeStatus.ACTIVE,
        joined_at=date.today()
    )

    db.add(pod_lead)
    db.flush()

    # Create Employee
    employee = Employee(
        employee_code="EMP003",
        full_name="Test Employee",
        email="employee@example.com",
        pod_id=pod.pod_id,
        status=EmployeeStatus.ACTIVE,
        joined_at=date.today()
    )

    db.add(employee)
    db.flush()

    # Assign Pod Lead to the Pod
    pod.pod_lead_id = pod_lead.employee_id

    # Create Pod Lead Account
    pod_lead_user = UserAccount(
        employee_id=pod_lead.employee_id,
        password_hash=hash_password("PodLead@12345"),
        role=UserRole.POD_LEAD,
        is_active=True
    )

    # Create Employee Account
    employee_user = UserAccount(
        employee_id=employee.employee_id,
        password_hash=hash_password("Employee@12345"),
        role=UserRole.EMPLOYEE,
        is_active=True
    )

    db.add_all([pod_lead_user, employee_user])

    db.commit()

    print("Two test accounts created successfully!")

    print("\nPOD LEAD")
    print("Email: podlead@example.com")
    print("Password: PodLead@12345")

    print("\nEMPLOYEE")
    print("Email: employee@example.com")
    print("Password: Employee@12345")

except Exception as e:
    db.rollback()
    print("Error creating test accounts:", e)
    raise

finally:
    db.close()
