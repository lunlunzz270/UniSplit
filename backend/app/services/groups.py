from ..core.database import SessionLocal
from ..repositories.groups import GroupRepository
from ..schemas.groups import GroupCreate


def create_group(group_in: GroupCreate, creator_id: int):
    db = SessionLocal()
    try:
        return GroupRepository(db).create_group(group_in, creator_id)
    finally:
        db.close()


def add_user_to_group(group_id: int, user_id: int, role: str = "MEMBER"):
    db = SessionLocal()
    try:
        return GroupRepository(db).add_user_to_group(group_id=group_id, user_id=user_id, role=role)
    finally:
        db.close()


def get_user_groups(user_id: int):
    db = SessionLocal()
    try:
        return GroupRepository(db).get_user_groups(user_id)
    finally:
        db.close()
