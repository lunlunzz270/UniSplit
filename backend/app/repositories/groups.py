from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.groups import Group, GroupMember
from ..schemas.groups import GroupCreate
from .activity_logs import ActivityLogRepository


class GroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_group_by_name(self, name: str) -> Group | None:
        return self.db.query(Group).filter(Group.name == name).first()

    def get_group_by_id(self, group_id: int) -> Group | None:
        return self.db.query(Group).filter(Group.id == group_id).first()

    def get_or_create_group_by_name(self, group_in: GroupCreate, creator_id: int) -> Group:
        existing = self.get_group_by_name(group_in.name)
        if existing:
            return existing
        return self.create_group(group_in, creator_id)

    def get_group_member(self, group_id: int, user_id: int) -> GroupMember | None:
        return (
            self.db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
            .first()
        )

    def create_group(self, group_in: GroupCreate, creator_id: int) -> Group:
        """Create a new group and automatically assign the creator as the group ADMIN."""
        try:
            db_group = Group(
                name=group_in.name,
                description=group_in.description,
                created_by=creator_id,
            )
            self.db.add(db_group)
            self.db.flush()

            db_member = GroupMember(
                group_id=db_group.id,
                user_id=creator_id,
                role="ADMIN",
            )
            self.db.add(db_member)

            ActivityLogRepository(self.db).create_log(
                group_id=db_group.id,
                user_id=creator_id,
                action_type="group_created",
                description=f"Group '{db_group.name}' created",
                ref_id=db_group.id,
            )

            self.db.commit()
            self.db.refresh(db_group)
            return db_group
        except SQLAlchemyError:
            self.db.rollback()
            raise

    def add_user_to_group(
        self,
        group_id: int,
        user_id: int,
        role: str = "MEMBER",
        commit: bool = True,
    ) -> GroupMember:
        """Add a user to a group via the bridge table."""
        existing = self.get_group_member(group_id, user_id)
        if existing:
            if role and existing.role != role:
                existing.role = role
                if commit:
                    self.db.commit()
                self.db.refresh(existing)
            return existing

        db_member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role
        )
        self.db.add(db_member)
        self.db.flush()
        if commit:
            self.db.commit()
        self.db.refresh(db_member)
        return db_member

    def remove_user_from_group(self, group_id: int, user_id: int, commit: bool = True) -> bool:
        member = self.get_group_member(group_id, user_id)
        if not member:
            return False
        self.db.delete(member)
        if commit:
            self.db.commit()
        return True

    def count_group_admins(self, group_id: int) -> int:
        return (
            self.db.query(GroupMember)
            .filter(GroupMember.group_id == group_id, GroupMember.role == "ADMIN")
            .count()
        )

    def is_group_admin(self, group_id: int, user_id: int) -> bool:
        group = self.get_group_by_id(group_id)
        if group and group.created_by == user_id:
            return True
        member = self.get_group_member(group_id, user_id)
        return bool(member and member.role == "ADMIN")

    def get_user_groups(self, user_id: int):
        """Fetch all groups a user is participating in (using a SQL JOIN)."""
        return self.db.query(Group).join(GroupMember).filter(GroupMember.user_id == user_id).all()
