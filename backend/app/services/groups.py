from ..core.database import SessionLocal
from ..repositories.activity_logs import ActivityLogRepository
from ..repositories.groups import GroupRepository
from ..repositories.users import UserRepository
from ..schemas.groups import GroupCreate


def create_group(group_in: GroupCreate, creator_id: int):
    db = SessionLocal()
    try:
        return GroupRepository(db).create_group(group_in, creator_id)
    finally:
        db.close()


def get_group_by_id(group_id: int):
    db = SessionLocal()
    try:
        return GroupRepository(db).get_group_by_id(group_id)
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


def get_group_members(group_id: int, user_id: int):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        group = group_repo.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        if not group_repo.get_group_member(group_id, user_id):
            raise ValueError("User must belong to the group")
        return group_repo.get_group_members(group_id)
    finally:
        db.close()


def can_manage_group(group_id: int, user_id: int) -> bool:
    db = SessionLocal()
    try:
        return GroupRepository(db).is_group_admin(group_id, user_id)
    finally:
        db.close()


def join_group(group_id: int, user_id: int, role: str = "MEMBER"):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        user_repo = UserRepository(db)

        group = group_repo.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        if not user_repo.get_user_by_id(user_id):
            raise ValueError("User not found")

        existing = group_repo.get_group_member(group_id, user_id)
        member = group_repo.add_user_to_group(group_id=group_id, user_id=user_id, role="MEMBER", commit=False)
        member_data = {
            "id": member.id,
            "group_id": member.group_id,
            "user_id": member.user_id,
            "role": member.role,
        }
        if existing is None:
            ActivityLogRepository(db).create_log(
                group_id=group_id,
                user_id=user_id,
                action_type="group_joined",
                description=f"User {user_id} joined group '{group.name}'",
                ref_id=group_id,
            )
            db.commit()
            return member_data, True

        db.commit()
        return member_data, False
    finally:
        db.close()


def leave_group(group_id: int, user_id: int):
    db = SessionLocal()
    try:
        group_repo = GroupRepository(db)
        user_repo = UserRepository(db)

        group = group_repo.get_group_by_id(group_id)
        if not group:
            raise ValueError("Group not found")
        if not user_repo.get_user_by_id(user_id):
            raise ValueError("User not found")

        member = group_repo.get_group_member(group_id, user_id)
        if not member:
            raise ValueError("User is not a member of this group")

        if member.role == "ADMIN" and group_repo.count_group_admins(group_id) <= 1:
            raise ValueError("Group must have at least one admin")

        removed = group_repo.remove_user_from_group(group_id, user_id, commit=False)
        if not removed:
            raise ValueError("Unable to remove user from group")

        ActivityLogRepository(db).create_log(
            group_id=group_id,
            user_id=user_id,
            action_type="group_left",
            description=f"User {user_id} left group '{group.name}'",
            ref_id=group_id,
        )
        db.commit()
        return {"group_id": group_id, "user_id": user_id}
    finally:
        db.close()
