from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CompanyProfileBase(BaseModel):
    profile_name: str = Field(..., min_length=1, max_length=255)
    profile_data: Optional[Dict[str, Any]] = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(BaseModel):
    profile_name: Optional[str] = Field(None, min_length=1, max_length=255)
    profile_data: Optional[Dict[str, Any]] = None


class CompanyProfile(CompanyProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyProfileList(BaseModel):
    profiles: list[CompanyProfile]
    total: int