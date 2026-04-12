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
