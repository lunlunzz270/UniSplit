from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    paid_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    group = relationship("Group", back_populates="expenses")
    payer = relationship("User")
    participants = relationship("ExpenseParticipant", back_populates="expense", cascade="all, delete-orphan")


class ExpenseParticipant(Base):
    __tablename__ = "expense_participants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    share = Column(Numeric(10, 2), nullable=False)
    is_settled = Column(Boolean, default=False)

    expense = relationship("Expense", back_populates="participants")
    user = relationship("User")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    note = Column(Text, nullable=True)
    settled_at = Column(DateTime, server_default=func.now())

    group = relationship("Group")
    payer = relationship("User", foreign_keys=[payer_id])
    payee = relationship("User", foreign_keys=[payee_id])
