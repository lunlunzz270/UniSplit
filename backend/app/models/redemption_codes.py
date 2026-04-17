from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base
import enum

class CodeCategory(str, enum.Enum):
    CASH = "CASH"
    VIP = "VIP"

class RedemptionCode(Base):
    __tablename__ = "redemption_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(Enum(CodeCategory), nullable=False)
    value = Column(Numeric(10, 2), nullable=False) # Amount for CASH, Days for VIP
    is_used = Column(Boolean, default=False)
    used_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    used_by = relationship("User")
