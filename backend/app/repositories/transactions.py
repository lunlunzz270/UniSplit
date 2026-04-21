from sqlalchemy.orm import Session
from ..models.transactions import Transaction
from ..models.users import User
from math import ceil

class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, user_id: int, type: str, amount: float, description: str):
        db_transaction = Transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            description=description
        )
        self.db.add(db_transaction)
        self.db.commit()
        self.db.refresh(db_transaction)
        return db_transaction

    def get_paged_transactions(self, type: str = None, page: int = 1, limit: int = 10, search: str = None):
        query = self.db.query(Transaction, User.full_name, User.email).join(User, Transaction.user_id == User.id)
        if type:
            query = query.filter(Transaction.type == type)
        
        if search:
            like = f"%{search}%"
            query = query.filter(
                (User.full_name.ilike(like)) | (User.email.ilike(like))
            )
        
        total = query.count()
        total_pages = ceil(total / limit) if total > 0 else 1
        
        offset = (page - 1) * limit
        results = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
        
        transactions_list = []
        for trans, full_name, email in results:
            transactions_list.append({
                "id": trans.id,
                "user_id": trans.user_id,
                "full_name": full_name,
                "email": email,
                "type": trans.type,
                "amount": float(trans.amount),
                "description": trans.description,
                "created_at": trans.created_at.isoformat()
            })
            
        return {
            "transactions": transactions_list,
            "total_count": total,
            "total_pages": total_pages,
            "current_page": page
        }
