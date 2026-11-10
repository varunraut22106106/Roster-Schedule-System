
from enum import Enum


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class CompOffTransactionType(str, Enum):
    CREDIT = "credit"
    REQUEST = "request"
    APPROVED_USAGE = "approved_usage"
    REJECTED = "rejected"


class ShiftType(str, Enum):
    PREDEFINED = "predefined"
    CUSTOM = "custom"


class DayStatus(str, Enum):
    WORKING = "working"
    WEEKLY_OFF = "weekly_off"
    LEAVE = "leave"
    COMP_OFF = "comp_off"
    HOLIDAY = "holiday"
    UNAVAILABLE = "unavailable"


class GenerationStatus(str, Enum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    UNKNOWN = "unknown"
    MODEL_INVALID = "model_invalid"


class RosterStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ConflictStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ConflictType(str, Enum):
    COVERAGE_GAP = "coverage_gap"
    OVERLAPPING_SHIFT = "overlapping_shift"
    WORKLOAD_LIMIT = "workload_limit"
    UNAVAILABILITY = "unavailability"
    OTHER = "other"


class AvailabilityType(str, Enum):
    FULL_DAY = "full_day"
    TIME_SLOT = "time_slot"


class NotificationType(str, Enum):
    ROSTER_PUBLISHED = "roster_published"
    ROSTER_UPDATED = "roster_updated"
    LEAVE_UPDATE = "leave_update"
    COMP_OFF_UPDATE = "comp_off_update"
    GENERAL = "general"

class StaffingRuleScope(str, Enum):
    DEFAULT = "default"
    WEEKDAY = "weekday"
    DATE = "date"
    
class HolidayScope(str, Enum):
    ORGANIZATION = "organization"
    BRAND = "brand"


class CompOffStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CREDITED = "credited"


class CompOffAction(str, Enum):
    CREDIT = "credit"
    USE_REQUEST = "use_request"
    USE_APPROVED = "use_approved"
    USE_REJECTED = "use_rejected"
    
class RosterPeriodStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class EditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    
    
class UserRole(str, Enum):
    OPERATIONS_MANAGER = "operations_manager"
    POD_LEAD = "pod_lead"
    EMPLOYEE = "employee"