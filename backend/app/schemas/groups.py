from pydantic import BaseModel, ConfigDict
from typing import Optional

class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None

class GroupCreate(GroupBase):
    pass

class GroupRead(GroupBase):
    id: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)