from decimal import Decimal, ROUND_DOWN
import csv
import io

from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..repositories.users import UserRepository
from ..repositories.expenses import ExpenseRepository
from ..models.expenses import Expense, ExpenseParticipant
from ..schemas.expenses import ExpenseCreate, ExpenseParticipantBase
from ..schemas.groups import GroupCreate


def _equal_split(amount: Decimal, count: int) -> list[Decimal]:
    if count <= 0:
        return []
    quantized = amount.quantize(Decimal("0.01"))
    base = (quantized / Decimal(count)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    shares = [base for _ in range(count)]
    remainder = quantized - sum(shares)
    shares[-1] = (shares[-1] + remainder).quantize(Decimal("0.01"))
    return shares


def create_expense_with_splits(group_id: int, expense_in: ExpenseCreate):
    db = SessionLocal()
    try:
        return ExpenseRepository(db).create_expense_with_splits(group_id, expense_in)
    finally:
        db.close()

def respond_to_expense(expense_id: int, user_id: int, status: str, appeal_reason: str | None = None):
    """Handle user response (accept/reject) to an expense split."""
    db = SessionLocal()
    try:
        from ..repositories.activity_logs import ActivityLogRepository
        expense_repo = ExpenseRepository(db)
        
        success = expense_repo.update_participant_status(expense_id, user_id, status, appeal_reason)
        if not success:
            raise ValueError("Expense or participant not found")

        # Log the action
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            action = "expense_appealed" if status == "rejected" else "expense_accepted"
            ActivityLogRepository(db).create_log(
                group_id=expense.group_id,
                user_id=user_id,
                action_type=action,
                description=f"User {status} expense '{expense.description}'" + (f": {appeal_reason}" if appeal_reason else ""),
                ref_id=expense_id
            )
        return success
    finally:
        db.close()

def resolve_expense_appeal(expense_id: int, participant_id: int, action: str):
    """Allow Payer to acknowledge or dismiss an appeal."""
    db = SessionLocal()
    try:
        from ..repositories.activity_logs import ActivityLogRepository
        expense_repo = ExpenseRepository(db)
        success = expense_repo.resolve_appeal(expense_id, participant_id, action)
        if not success:
            raise ValueError("Failed to resolve appeal")
            
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if expense:
            ActivityLogRepository(db).create_log(
                group_id=expense.group_id,
                user_id=expense.paid_by,
                action_type="expense_accepted", # Re-using existing for simplicity or add new
                description=f"Payer {action}ed appeal for expense '{expense.description}'",
                ref_id=expense_id
            )
        return success
    finally:
        db.close()

def list_expenses(user_id: int | None = None, is_admin: bool = False, search: str = "", category: str = "", group_name: str = "", start_date: str = "", end_date: str = "", limit: int | None = 10, offset: int = 0):
    db = SessionLocal()
    try:
        return ExpenseRepository(db).list_expenses(
            user_id=user_id,
            is_admin=is_admin,
            search=search,
            category=category,
            group_name=group_name,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )
    finally:
        db.close()


def export_expenses_csv(user_id: int | None = None, is_admin: bool = False, search: str = "", category: str = "", group_name: str = "", start_date: str = "", end_date: str = ""):
    expenses = list_expenses(
        user_id=user_id,
        is_admin=is_admin,
        search=search,
        category=category,
        group_name=group_name,
        start_date=start_date,
        end_date=end_date,
        limit=None,
        offset=0,
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "description",
        "amount",
        "category",
        "group_name",
        "payer",
        "date",
        "participant_summary",
    ])

    for expense in expenses:
        participants = []
        for participant in expense.get("participants", []):
            status_bits = [participant.get("status") or "unknown"]
            if participant.get("is_settled"):
                status_bits.append("settled")
            participant_label = f"{participant.get('name') or 'Unknown'}<{participant.get('email') or ''}>:{participant.get('share', 0):.2f}"
            participants.append(f"{participant_label} ({', '.join(status_bits)})")

        writer.writerow([
            expense.get("id"),
            expense.get("description"),
            f"{float(expense.get('amount', 0)):.2f}",
            expense.get("category"),
            expense.get("group_name"),
            expense.get("payer"),
            expense.get("date"),
            " | ".join(participants),
        ])

    return output.getvalue()


def record_expense(
    group_name: str,
    description: str,
    amount: Decimal,
    category: str,
    payer_email: str,
    participant_emails: list[str],
):
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        group_repo = GroupRepository(db)
        expense_repo = ExpenseRepository(db)

        payer = user_repo.get_user_by_email(payer_email)
        if not payer:
            raise ValueError("Payer must have an account first")
        
        if payer.is_admin:
            raise ValueError("Administrative users are not allowed to participate in or pay for expenses.")

        participant_users = []
        seen_emails: set[str] = set()
        for email in participant_emails:
            normalized = email.strip().lower()
            if not normalized or normalized in seen_emails:
                continue
            seen_emails.add(normalized)
            user = user_repo.get_user_by_email(normalized)
            if not user:
                raise ValueError(f"Participant not found: {normalized}")
            
            if user.is_admin:
                raise ValueError(f"User {normalized} is an administrator and cannot be added to an expense.")
            
            participant_users.append(user)

        if not participant_users:
            raise ValueError("At least one participant is required")

        group = group_repo.get_or_create_group_by_name(
            GroupCreate(name=group_name),
            creator_id=payer.id,
        )

        group_repo.add_user_to_group(group.id, payer.id)
        for user in participant_users:
            group_repo.add_user_to_group(group.id, user.id)

        # Logic Update: Calculate share for ALL, but only record debt for OTHERS
        total_people = len(participant_users)
        shares = _equal_split(Decimal(amount), total_people)
        
        # Filter out the payer from the participants list to be saved in DB
        debt_participants = []
        for user, share in zip(participant_users, shares, strict=True):
            if user.id != payer.id:
                debt_participants.append(
                    ExpenseParticipantBase(user_id=user.id, share=share)
                )

        expense = expense_repo.create_expense_with_splits(
            group.id,
            ExpenseCreate(
                amount=Decimal(amount),
                category=category,
                description=description,
                paid_by=payer.id,
                participants=debt_participants,
            ),
        )
        return expense
    finally:
        db.close()
