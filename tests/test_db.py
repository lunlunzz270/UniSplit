from backend.app.models.users import User
from backend.app.models.groups import Group
from backend.app.models.expenses import Expense


def test_database_mapping_uses_isolated_memory_db(in_memory_session):
    db = in_memory_session

    assert db.query(User).count() == 0
    assert db.query(Group).count() == 0
    assert db.query(Expense).count() == 0
