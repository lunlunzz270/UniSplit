from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Text, UniqueConstraint
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
    __table_args__ = (UniqueConstraint("expense_id", "user_id", name="uq_expense_user"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    share = Column(Numeric(10, 2), nullable=False)
    is_settled = Column(Boolean, default=False)
    status = Column(String(20), default="pending") # pending, accepted, rejected, paid
    appeal_reason = Column(Text, nullable=True)
    last_reminder_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)

    expense = relationship("Expense", back_populates="participants")
    user = relationship("User")


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    expense_id = Column(Integer, ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False)
    payer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default="pending") # pending, accepted, rejected, paid, cancelled
    rejection_message = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    last_reminder_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0)
    settled_at = Column(DateTime, nullable=True)

    group = relationship("Group")
    expense = relationship("Expense")
    payer = relationship("User", foreign_keys=[payer_id], back_populates="settlements_paid")
    payee = relationship("User", foreign_keys=[payee_id], back_populates="settlements_received")
