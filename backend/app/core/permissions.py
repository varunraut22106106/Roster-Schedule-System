
from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.enums import UserRole


def require_role(*allowed_roles: UserRole):

    def role_checker(current_user=Depends(get_current_user)):

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource"
            )

        return current_user

    return role_checker


# Predefined role dependencies

require_operations_manager = require_role(
    UserRole.OPERATIONS_MANAGER
)

require_pod_lead = require_role(
    UserRole.POD_LEAD
)

require_employee = require_role(
    UserRole.EMPLOYEE
)

require_manager_or_pod_lead = require_role(
    UserRole.OPERATIONS_MANAGER,
    UserRole.POD_LEAD
)

require_all_authenticated = require_role(
    UserRole.OPERATIONS_MANAGER,
    UserRole.POD_LEAD,
    UserRole.EMPLOYEE
)