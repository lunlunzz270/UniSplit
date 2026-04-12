from ..core.database import SessionLocal
from ..repositories.activity_logs import ActivityLogRepository


def get_group_activity_logs(group_id: int):
    db = SessionLocal()
    try:
        logs = ActivityLogRepository(db).get_group_logs(group_id)
        return [
            {
                "id": log.id,
                "group_id": log.group_id,
                "user_id": log.user_id,
                "user_name": log.user.full_name if log.user else None,
                "action_type": log.action_type,
                "description": log.description,
                "ref_id": log.ref_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    finally:
        db.close()
