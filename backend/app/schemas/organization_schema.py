
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


# ---------------- BRAND ----------------

class BrandCreate(BaseModel):
    brand_name: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class BrandUpdate(BaseModel):
    brand_name: str | None = Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None


class BrandResponse(BaseModel):
    brand_id: UUID
    brand_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- POD ----------------

class PodCreate(BaseModel):
    pod_name: str = Field(min_length=1, max_length=150)
    pod_lead_id: UUID | None = None
    is_active: bool = True


class PodUpdate(BaseModel):
    pod_name: str | None = Field(default=None, min_length=1, max_length=150)
    pod_lead_id: UUID | None = None
    is_active: bool | None = None


class PodResponse(BaseModel):
    pod_id: UUID
    pod_name: str
    pod_lead_id: UUID | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------- PROCESS ----------------

class ProcessCreate(BaseModel):
    brand_id: UUID
    process_name: str = Field(min_length=1, max_length=150)
    is_active: bool = True


class ProcessUpdate(BaseModel):
    brand_id: UUID | None = None
    process_name: str | None = Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None


class ProcessResponse(BaseModel):
    process_id: UUID
    brand_id: UUID
    process_name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
