from pydantic import BaseModel, ConfigDict, Field


class ReminderCreate(BaseModel):
    recipient_id: int
    message: str = Field(min_length=1, max_length=500)


class ReminderRead(BaseModel):
    id: int
    group_id: int
    sender_id: int
    recipient_id: int
    message: str
    is_read: bool

    model_config = ConfigDict(from_attributes=True)
