from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from backend.app.models.expenses import Expense, ExpenseParticipant
from backend.app.schemas.expenses import ExpenseCreate


class ExpenseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_expense_with_splits(self, group_id: int, expense_in: ExpenseCreate) -> Expense:
        """Use a database transaction to save both the main expense and split details simultaneously."""
        try:
            # 1. Create the main expense record
            db_expense = Expense(
                group_id=group_id,
                description=expense_in.description,
                amount=expense_in.amount,
                paid_by=expense_in.paid_by,
                category=expense_in.category
            )
            self.db.add(db_expense)
            # Use flush() instead of commit() to generate the db_expense.id for foreign keys
            # without permanently writing to the database yet.
            self.db.flush()

            # 2. Iterate and create specific split details for each participant
            for participant_data in expense_in.participants:
                db_participant = ExpenseParticipant(
                    expense_id=db_expense.id,  # Link to the newly generated expense ID
                    user_id=participant_data.user_id,
                    share=participant_data.share,
                    is_settled=False
                )
                self.db.add(db_participant)

            # 3. If all steps succeed, commit the entire transaction
            self.db.commit()
            self.db.refresh(db_expense)
            return db_expense

        except SQLAlchemyError as e:
            # If any database error occurs (e.g., foreign key violation), rollback everything
            # to maintain ledger consistency.
            self.db.rollback()
            raise e

    def get_group_expenses(self, group_id: int):
        """Fetch all expense history for a specific group."""
        return self.db.query(Expense).filter(Expense.group_id == group_id).order_by(Expense.created_at.desc()).all()