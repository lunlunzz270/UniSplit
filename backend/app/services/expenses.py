from decimal import Decimal, ROUND_DOWN

from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..repositories.users import UserRepository
from ..repositories.expenses import ExpenseRepository
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


def list_expenses(user_id: int | None = None, is_admin: bool = False, search: str = "", category: str = "", group_name: str = ""):
    db = SessionLocal()
    try:
        return ExpenseRepository(db).list_expenses(
            user_id=user_id,
            is_admin=is_admin,
            search=search,
            category=category,
            group_name=group_name
        )
    finally:
        db.close()


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

        shares = _equal_split(Decimal(amount), len(participant_users))
        expense = expense_repo.create_expense_with_splits(
            group.id,
            ExpenseCreate(
                amount=Decimal(amount),
                category=category,
                description=description,
                paid_by=payer.id,
                participants=[
                    ExpenseParticipantBase(user_id=user.id, share=share)
                    for user, share in zip(participant_users, shares, strict=True)
                ],
            ),
        )
        return expense
    finally:
        db.close()
