from backend.app.core.database import SessionLocal
from backend.app.models.users import User
from backend.app.models.groups import Group
from backend.app.models.expenses import Expense


def test_database_mapping():
    db = SessionLocal()
    try:
        print("🔌 Connecting to MySQL database...")

        # Test 1: Query Users
        user_count = db.query(User).count()
        print(f"✅ Connection successful! Found {user_count} records in 'users' table.")

        # Test 2: Query Groups
        group_count = db.query(Group).count()
        print(f"✅ Connection successful! Found {group_count} records in 'groups' table.")

        # Test 3: Query Expenses
        expense_count = db.query(Expense).count()
        print(f"✅ Connection successful! Found {expense_count} records in 'expenses' table.")

        print("🚀 All SQLAlchemy models are perfectly mapped to the database tables!")

    except Exception as e:
        print("❌ Database connection or mapping failed. Error details:")
        print(str(e))
    finally:
        db.close()


if __name__ == "__main__":
    test_database_mapping()