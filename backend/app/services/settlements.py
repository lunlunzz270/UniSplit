from ..core.database import SessionLocal
from ..repositories.settlements import SettlementRepository
from ..schemas.settlements import SettlementCreate


def create_settlement(group_id: int, settlement_in: SettlementCreate):
    db = SessionLocal()
    try:
        return SettlementRepository(db).create_settlement(group_id, settlement_in)
    finally:
        db.close()


def get_group_settlements(group_id: int):
    db = SessionLocal()
    try:
        return SettlementRepository(db).get_group_settlements(group_id)
    finally:
        db.close()
