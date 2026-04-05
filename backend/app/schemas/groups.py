from pydantic import BaseModel
from typing import Optional

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupRead(GroupBase):
    id: int
    created_by: int

    class Config:
        from_attributes = True