from sqlalchemy.orm import Session

from ..models.activity_log import ActivityLog


class ActivityLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(
        self,
        group_id: int,
        user_id: int,
        action_type: str,
        description: str,
        ref_id: int | None = None,
    ) -> ActivityLog:
        log = ActivityLog(
            group_id=group_id,
            user_id=user_id,
            action_type=action_type,
            description=description,
            ref_id=ref_id,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def get_group_logs(self, group_id: int):
        return (
            self.db.query(ActivityLog)
            .filter(ActivityLog.group_id == group_id)
            .order_by(ActivityLog.created_at.desc())
            .all()
        )

    def get_user_logs(self, user_id: int, is_admin: bool = False, limit: int = 10, offset: int = 0):
        from ..models.groups import GroupMember
        query = self.db.query(ActivityLog)
        
        if not is_admin:
            # Get group IDs the user belongs to
            user_group_ids = self.db.query(GroupMember.group_id).filter(GroupMember.user_id == user_id).all()
            user_group_ids = [g[0] for g in user_group_ids]
            query = query.filter(ActivityLog.group_id.in_(user_group_ids))
            
        return (
            query.order_by(ActivityLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
