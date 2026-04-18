import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.core.database import Base


@pytest.fixture()
def in_memory_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def api_client(monkeypatch, session_factory):
    from backend.app.core import database as database_module
    monkeypatch.setattr("backend.app.services.auth.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.expenses.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.groups.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.settlements.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.activity_logs.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.reminders.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.admin.SessionLocal", session_factory)
    monkeypatch.setattr("backend.app.services.redemption.SessionLocal", session_factory)
    monkeypatch.setattr(database_module, "SessionLocal", session_factory)

    from backend.main import app

    return app.test_client()


@pytest.fixture()
def sqlite_session_factory():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    import backend.app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def patched_sessionlocal(sqlite_session_factory, monkeypatch):
    from backend.app.core import database as database_module
    from backend.app.services import auth as auth_service
    from backend.app.services import expenses as expenses_service
    from backend.app.services import groups as groups_service
    from backend.app.services import settlements as settlements_service
    from backend.app.services import reminders as reminders_service
    from backend.app.services import admin as admin_service
    from backend.app.services import redemption as redemption_service

    monkeypatch.setattr(database_module, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(auth_service, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(expenses_service, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(groups_service, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(settlements_service, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(reminders_service, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(admin_service, "SessionLocal", sqlite_session_factory)
    monkeypatch.setattr(redemption_service, "SessionLocal", sqlite_session_factory)
    return sqlite_session_factory


@pytest.fixture()
def app_client(patched_sessionlocal):
    from backend.main import app

    return app.test_client()
