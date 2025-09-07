from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class FrameworkBase(BaseModel):
    name: str = Field(..., description="Framework name")
    description: Optional[str] = Field(None, description="Framework description")
    category: str = Field(..., description="Framework category (e.g., strategy, analysis)")
    difficulty_level: str = Field("beginner", description="Difficulty level: beginner, intermediate, advanced")
    estimated_duration: int = Field(..., description="Estimated completion time in minutes")
    is_premium: bool = Field(False, description="Whether this is a premium feature")
    micro_content: Optional[Dict[str, Any]] = Field(None, description="Learning content data")


class FrameworkCreate(FrameworkBase):
    pass


class FrameworkUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_premium: Optional[bool] = None
    micro_content: Optional[Dict[str, Any]] = None


class Framework(FrameworkBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FrameworkList(BaseModel):
    frameworks: List[Framework]
    total: int
    page: int
    limit: int


class FrameworkContent(BaseModel):
    id: str
    name: str
    description: Optional[str]
    category: str
    difficulty_level: str
    estimated_duration: int
    is_premium: bool
    micro_content: Optional[Dict[str, Any]]
    
    class Config:
        from_attributes = True