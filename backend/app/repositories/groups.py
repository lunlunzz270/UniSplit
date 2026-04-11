from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.groups import Group, GroupMember
from ..schemas.groups import GroupCreate
from .activity_logs import ActivityLogRepository


class GroupRepository:
    def __init__(self, db: Session):
        self.db = db

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

    def add_user_to_group(self, group_id: int, user_id: int, role: str = "MEMBER") -> GroupMember:
        """Add a user to a group via the bridge table."""
        db_member = GroupMember(
            group_id=group_id,
            user_id=user_id,
            role=role
        )
        self.db.add(db_member)
        self.db.commit()
        self.db.refresh(db_member)
        return db_member

    def get_user_groups(self, user_id: int):
        """Fetch all groups a user is participating in (using a SQL JOIN)."""
        return self.db.query(Group).join(GroupMember).filter(GroupMember.user_id == user_id).all()
