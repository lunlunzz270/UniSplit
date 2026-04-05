import pytest
from pydantic import ValidationError
from decimal import Decimal
from backend.app.schemas.users import RegisterRequest, UserCreate
from backend.app.schemas.expenses import ExpenseCreate, ExpenseParticipantBase


# Test Suite: User & Authentication Schemas
def test_register_request_valid_data():
    """Test successful creation of a RegisterRequest with valid data."""
    valid_data = {
        "name": "John Doe",
        "email": "john.doe@duke.edu",
        "password": "SecurePassword123!"
    }
    user_req = RegisterRequest(**valid_data)

    assert user_req.name == "John Doe"
    assert user_req.email == "john.doe@duke.edu"
    assert user_req.password == "SecurePassword123!"


def test_register_request_invalid_email():
    """Test that an invalid email format raises a ValidationError."""
    invalid_data = {
        "name": "John Doe",
        "email": "not-an-email",  # Invalid email format
        "password": "SecurePassword123!"
    }

    with pytest.raises(ValidationError) as excinfo:
        RegisterRequest(**invalid_data)

    assert "email" in str(excinfo.value).lower()


def test_user_create_missing_required_field():
    """Test that missing a required field (e.g., password) raises an error."""
    invalid_data = {
        "full_name": "Jane Smith",
        "email": "jane@example.com"
        # Missing 'password'
    }

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**invalid_data)

    assert "password" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)


# Test Suite: Expense & Split Schemas
def test_expense_create_valid_data():
    """Test successful creation of an ExpenseCreate model with nested participants."""
    valid_data = {
        "amount": Decimal("150.75"),
        "category": "Groceries",
        "description": "Weekly grocery run",
        "paid_by": 1,
        "participants": [
            {"user_id": 1, "share": Decimal("50.25")},
            {"user_id": 2, "share": Decimal("100.50")}
        ]
    }

    expense = ExpenseCreate(**valid_data)

    assert expense.amount == Decimal("150.75")
    assert expense.category == "Groceries"
    assert len(expense.participants) == 2
    assert expense.participants[0].share == Decimal("50.25")


def test_expense_amount_zero_or_negative():
    """Test that amounts <= 0 are rejected due to the Field(gt=0) constraint."""
    # Test Negative Amount
    with pytest.raises(ValidationError) as excinfo_negative:
        ExpenseCreate(
            amount=Decimal("-10.00"),
            category="Dining",
            paid_by=1,
            participants=[]
        )
    assert "greater than 0" in str(excinfo_negative.value)

    # Test Zero Amount
    with pytest.raises(ValidationError) as excinfo_zero:
        ExpenseCreate(
            amount=Decimal("0.00"),
            category="Dining",
            paid_by=1,
            participants=[]
        )
    assert "greater than 0" in str(excinfo_zero.value)


def test_expense_participant_precision():
    """Test that the Decimal precision correctly parses string financial inputs."""
    participant_data = {
        "user_id": 3,
        "share": "33.33"  # Passing as string, Pydantic should cast to Decimal
    }

    participant = ExpenseParticipantBase(**participant_data)

    assert isinstance(participant.share, Decimal)
    assert participant.share == Decimal("33.33")


def test_expense_missing_participants_list():
    """Test that creating an expense without the participants list fails."""
    invalid_data = {
        "amount": Decimal("50.00"),
        "category": "Travel",
        "paid_by": 2
        # Missing 'participants'
    }

    with pytest.raises(ValidationError) as excinfo:
        ExpenseCreate(**invalid_data)

    assert "participants" in str(excinfo.value)
    assert "Field required" in str(excinfo.value)