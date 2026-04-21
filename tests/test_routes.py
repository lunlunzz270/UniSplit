import csv
import io

import pytest


def test_auth_and_expense_routes(api_client):
    register = api_client.post(
        "/api/register",
        json={"name": "Route User", "email": "route@example.com", "password": "pwd123"},
    )
    assert register.status_code == 201
    assert register.get_json()["email"] == "route@example.com"
    assert register.get_json()["session"]["token"]

    login = api_client.post(
        "/api/login",
        json={"email": "route@example.com", "password": "pwd123"},
    )
    assert login.status_code == 200
    assert login.get_json()["name"] == "Route User"
    session_token = login.get_json()["session"]["token"]

    me = api_client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {session_token}"},
    )
    assert me.status_code == 200
    assert me.get_json()["email"] == "route@example.com"

    teammate = api_client.post(
        "/api/register",
        json={"name": "Teammate", "email": "team@example.com", "password": "pwd123"},
    ).get_json()

    expense = api_client.post(
        "/api/expenses",
        headers={"Authorization": f"Bearer {session_token}"},
        json={
            "group_name": "Sprint 5 Trip",
            "description": "Airport taxi",
            "amount": "24.00",
            "category": "Travel",
            "payer_email": "route@example.com",
            "participant_emails": ["route@example.com", teammate["email"]],
        },
    )
    assert expense.status_code == 201
    assert expense.get_json()["description"] == "Airport taxi"

    history = api_client.get("/api/expenses", headers={"Authorization": f"Bearer {session_token}"})
    assert history.status_code == 200
    records = history.get_json()["expenses"]
    assert len(records) == 1
    assert records[0]["group_name"] == "Sprint 5 Trip"

    email_search = api_client.get(
        "/api/expenses",
        headers={"Authorization": f"Bearer {session_token}"},
        query_string={"search": "team@example.com"},
    )
    assert email_search.status_code == 200
    assert len(email_search.get_json()["expenses"]) == 1

    logout = api_client.post(
        "/api/logout",
        json={"session_token": session_token},
    )
    assert logout.status_code == 200


def test_expense_export_route_requires_authentication(api_client):
    res = api_client.get("/api/expenses/export")
    assert res.status_code == 401
    assert res.get_json()["error"]


def test_expense_export_route_returns_csv_and_applies_filters(api_client):
    user = api_client.post(
        "/api/register",
        json={"name": "Exporter", "email": "exporter@example.com", "password": "pwd123"},
    ).get_json()
    teammate = api_client.post(
        "/api/register",
        json={"name": "Teammate", "email": "export.team@example.com", "password": "pwd123"},
    ).get_json()
    other = api_client.post(
        "/api/register",
        json={"name": "Other", "email": "export.other@example.com", "password": "pwd123"},
    ).get_json()

    first_expense = api_client.post(
        "/api/expenses",
        headers={"Authorization": f"Bearer {user['session']['token']}"},
        json={
            "group_name": "Export Group",
            "description": "Airport taxi",
            "amount": "24.00",
            "category": "Travel",
            "payer_email": user["email"],
            "participant_emails": [user["email"], teammate["email"]],
        },
    )
    assert first_expense.status_code == 201

    second_expense = api_client.post(
        "/api/expenses",
        headers={"Authorization": f"Bearer {user['session']['token']}"},
        json={
            "group_name": "Another Group",
            "description": "Lunch",
            "amount": "12.50",
            "category": "Food",
            "payer_email": user["email"],
            "participant_emails": [user["email"], other["email"]],
        },
    )
    assert second_expense.status_code == 201

    export_res = api_client.get(
        "/api/expenses/export",
        headers={"Authorization": f"Bearer {user['session']['token']}"},
        query_string={
            "search": "taxi",
            "category": "Travel",
            "group_name": "Export Group",
        },
    )
    assert export_res.status_code == 200
    assert export_res.mimetype == "text/csv"
    assert "attachment" in export_res.headers["Content-Disposition"]
    assert "expense_report" in export_res.headers["Content-Disposition"]

    csv_rows = list(csv.DictReader(io.StringIO(export_res.get_data(as_text=True))))
    assert len(csv_rows) == 1
    row = csv_rows[0]
    assert row["description"] == "Airport taxi"
    assert row["category"] == "Travel"
    assert row["group_name"] == "Export Group"
    assert row["payer"] == "Exporter"
    assert row["id"]
    assert row["date"]
    assert row["participant_summary"]

    future_res = api_client.get(
        "/api/expenses/export",
        headers={"Authorization": f"Bearer {user['session']['token']}"},
        query_string={"start_date": "2999-01-01"},
    )
    assert future_res.status_code == 200
    future_rows = list(csv.DictReader(io.StringIO(future_res.get_data(as_text=True))))
    assert len(future_rows) == 0


def test_group_join_and_leave_routes_repeat_and_delete(api_client):
    creator = api_client.post(
        "/api/register",
        json={"name": "Creator", "email": "join.creator@example.com", "password": "pwd123"},
    ).get_json()
    member = api_client.post(
        "/api/register",
        json={"name": "Member", "email": "join.member@example.com", "password": "pwd123"},
    ).get_json()

    group_res = api_client.post(
        "/api/groups",
        json={"name": "Join Group", "description": "Sprint 6", "creator_id": creator["id"]},
    )
    assert group_res.status_code == 201
    group_id = group_res.get_json()["id"]

    join_res = api_client.post(
        f"/api/groups/{group_id}/join",
        json={"user_id": member["id"]},
    )
    assert join_res.status_code == 201
    assert join_res.get_json()["member"]["user_id"] == member["id"]

    leave_res = api_client.post(
        f"/api/groups/{group_id}/leave",
        json={"user_id": member["id"]},
    )
    assert leave_res.status_code == 200
    assert leave_res.get_json()["user_id"] == member["id"]


def test_group_settlement_and_activity_log_routes(api_client, session_factory):
    creator = api_client.post(
        "/api/register",
        json={"name": "Creator", "email": "creator@example.com", "password": "pwd123"},
    ).get_json()
    teammate = api_client.post(
        "/api/register",
        json={"name": "Teammate", "email": "teammate@example.com", "password": "pwd123"},
    ).get_json()

    # Manual balance top-up for teammate to allow settlement
    from backend.app.repositories.users import UserRepository
    db = session_factory()
    UserRepository(db).update_balance(teammate["id"], 50.00)
    db.close()

    group_res = api_client.post(
        "/api/groups",
        json={"name": "Route Group", "description": "Sprint 5", "creator_id": creator["id"]},
    )
    assert group_res.status_code == 201
    group_id = group_res.get_json()["id"]

    member_res = api_client.post(
        f"/api/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {creator['session']['token']}"},
        json={"user_id": teammate["id"], "role": "MEMBER"},
    )
    assert member_res.status_code == 201
    assert member_res.get_json()["user_id"] == teammate["id"]

    group_list = api_client.get(f"/api/users/{creator['id']}/groups")
    assert group_list.status_code == 200
    assert group_list.get_json()["groups"][0]["name"] == "Route Group"

    # Create an expense for the group so settlement can reference it
    expense_res = api_client.post(
        "/api/expenses",
        headers={"Authorization": f"Bearer {creator['session']['token']}"},
        json={
            "group_name": "Route Group",
            "description": "Lunch",
            "amount": "25.00",
            "category": "Food",
            "payer_email": creator["email"],
            "participant_emails": [creator["email"], teammate["email"]],
        },
    )
    assert expense_res.status_code == 201
    expense_id = expense_res.get_json()["id"]

    settlement_res = api_client.post(
        f"/api/groups/{group_id}/settlements",
        headers={"Authorization": f"Bearer {teammate['session']['token']}"},
        json={
            "expense_id": expense_id,
            "payer_id": teammate["id"],
            "payee_id": creator["id"],
            "amount": "12.50",
            "note": "Lunch split",
        },
    )
    assert settlement_res.status_code == 201
    assert settlement_res.get_json()["amount"] == 12.50

    logs = api_client.get(f"/api/groups/{group_id}/activity-logs", headers={"Authorization": f"Bearer {creator['session']['token']}"})
    assert logs.status_code == 200
    actions = [item["action_type"] for item in logs.get_json()["activity_logs"]]
    assert "group_created" in actions
    assert "settlement_recorded" in actions


def test_auth_session_me_and_logout_routes(api_client):
    register = api_client.post(
        "/api/register",
        json={"name": "Session User", "email": "session@example.com", "password": "pwd123"},
    )
    assert register.status_code == 201
    register_data = register.get_json()
    assert register_data["session"]["token"]

    login = api_client.post(
        "/api/login",
        json={"email": "session@example.com", "password": "pwd123"},
    )
    assert login.status_code == 200
    login_data = login.get_json()
    session_token = login_data["session"]["token"]

    me = api_client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {session_token}"},
    )
    assert me.status_code == 200
    assert me.get_json()["email"] == "session@example.com"

    logout = api_client.post(
        "/api/logout",
        headers={"X-Session-Token": session_token},
    )
    assert logout.status_code == 200

    me_after_logout = api_client.get(
        "/api/me",
        headers={"Authorization": f"Bearer {session_token}"},
    )
    assert me_after_logout.status_code == 401


def test_group_join_and_leave_routes(api_client):
    creator = api_client.post(
        "/api/register",
        json={"name": "Group Creator", "email": "group.creator@example.com", "password": "pwd123"},
    ).get_json()
    teammate = api_client.post(
        "/api/register",
        json={"name": "Group Member", "email": "group.member@example.com", "password": "pwd123"},
    ).get_json()

    group_res = api_client.post(
        "/api/groups",
        json={"name": "Sprint 6 Group", "description": "Join/leave test", "creator_id": creator["id"]},
    )
    assert group_res.status_code == 201
    group_id = group_res.get_json()["id"]

    join_res = api_client.post(
        f"/api/groups/{group_id}/join",
        json={"user_id": teammate["id"]},
    )
    assert join_res.status_code == 201
    assert join_res.get_json()["member"]["user_id"] == teammate["id"]

    repeat_join = api_client.post(
        f"/api/groups/{group_id}/join",
        json={"user_id": teammate["id"]},
    )
    assert repeat_join.status_code == 200
    assert repeat_join.get_json()["created"] is False

    leave_res = api_client.delete(
        f"/api/groups/{group_id}/leave",
        json={"user_id": teammate["id"]},
    )
    assert leave_res.status_code == 200
    assert leave_res.get_json()["group_id"] == group_id

    leave_again = api_client.delete(
        f"/api/groups/{group_id}/leave",
        json={"user_id": teammate["id"]},
    )
    assert leave_again.status_code == 400


def test_reminder_routes(api_client):
    sender = api_client.post(
        "/api/register",
        json={"name": "Sender", "email": "sender@example.com", "password": "pwd123"},
    ).get_json()
    recipient = api_client.post(
        "/api/register",
        json={"name": "Recipient", "email": "recipient@example.com", "password": "pwd123"},
    ).get_json()
    outsider = api_client.post(
        "/api/register",
        json={"name": "Outsider", "email": "outsider@example.com", "password": "pwd123"},
    ).get_json()

    group_res = api_client.post(
        "/api/groups",
        json={"name": "Reminder Group", "description": "Reminder test", "creator_id": sender["id"]},
    )
    assert group_res.status_code == 201
    group_id = group_res.get_json()["id"]

    join_res = api_client.post(
        f"/api/groups/{group_id}/join",
        json={"user_id": recipient["id"]},
    )
    assert join_res.status_code in (200, 201)

    reminder_res = api_client.post(
        f"/api/groups/{group_id}/reminders",
        headers={"Authorization": f"Bearer {sender['session']['token']}"},
        json={"recipient_id": recipient["id"], "message": "Please settle up"},
    )
    assert reminder_res.status_code == 201
    assert reminder_res.get_json()["recipient_id"] == recipient["id"]

    reminder_list = api_client.get(
        f"/api/groups/{group_id}/reminders",
        headers={"Authorization": f"Bearer {sender['session']['token']}"},
    )
    assert reminder_list.status_code == 200
    assert len(reminder_list.get_json()["reminders"]) == 1

    outsider_res = api_client.post(
        f"/api/groups/{group_id}/reminders",
        headers={"Authorization": f"Bearer {outsider['session']['token']}"},
        json={"recipient_id": recipient["id"], "message": "Blocked"},
    )
    assert outsider_res.status_code == 403


def test_group_members_route(api_client):
    owner = api_client.post(
        "/api/register",
        json={"name": "Owner", "email": "members.owner@example.com", "password": "pwd123"},
    ).get_json()
    member = api_client.post(
        "/api/register",
        json={"name": "Member", "email": "members.member@example.com", "password": "pwd123"},
    ).get_json()
    outsider = api_client.post(
        "/api/register",
        json={"name": "Outsider", "email": "members.outsider@example.com", "password": "pwd123"},
    ).get_json()

    group_res = api_client.post(
        "/api/groups",
        json={"name": "Members Group", "description": "Members test", "creator_id": owner["id"]},
    )
    assert group_res.status_code == 201
    group_id = group_res.get_json()["id"]

    join_res = api_client.post(
        f"/api/groups/{group_id}/join",
        json={"user_id": member["id"]},
    )
    assert join_res.status_code in (200, 201)

    list_res = api_client.get(
        f"/api/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {owner['session']['token']}"},
    )
    assert list_res.status_code == 200
    members = list_res.get_json()["members"]
    assert any(item["user_id"] == owner["id"] and item["email"] == owner["email"] for item in members)
    assert any(item["user_id"] == member["id"] and item["full_name"] == "Member" for item in members)

    outsider_res = api_client.get(
        f"/api/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {outsider['session']['token']}"},
    )
    assert outsider_res.status_code == 403


def test_admin_routes(api_client, session_factory):
    admin_user = api_client.post(
        "/api/register",
        json={"name": "Admin User", "email": "admin@unisplit.com", "password": "pwd123", "role": "admin"},
    ).get_json()
    regular_user = api_client.post(
        "/api/register",
        json={"name": "Regular User", "email": "regular@example.com", "password": "pwd123", "role": "user"},
    ).get_json()

    admin_headers = {"Authorization": f"Bearer {admin_user['session']['token']}"}
    user_headers = {"Authorization": f"Bearer {regular_user['session']['token']}"}

    admin_login = api_client.post(
        "/api/login",
        json={"email": "admin@unisplit.com", "password": "pwd123", "role": "admin"},
    )
    assert admin_login.status_code == 200
    assert admin_login.get_json()["role"] == "admin"

    list_res = api_client.get("/api/admin/users", headers=admin_headers)
    assert list_res.status_code == 200
    users = list_res.get_json()["users"]
    assert any(user["email"] == "regular@example.com" for user in users)

    overview_res = api_client.get("/api/admin/overview", headers=admin_headers)
    assert overview_res.status_code == 200
    assert overview_res.get_json()["total_users"] >= 2

    deny_res = api_client.get("/api/admin/users", headers=user_headers)
    assert deny_res.status_code == 403

    disable_res = api_client.post(f"/api/admin/users/{regular_user['id']}/disable", headers=admin_headers)
    assert disable_res.status_code == 200
    assert disable_res.get_json()["is_active"] is False
    assert disable_res.get_json()["role"] == "user"

    disabled_login = api_client.post(
        "/api/login",
        json={"email": "regular@example.com", "password": "pwd123", "role": "user"},
    )
    assert disabled_login.status_code == 401

    disabled_me = api_client.get("/api/me", headers=user_headers)
    assert disabled_me.status_code == 401

    restore_res = api_client.post(f"/api/admin/users/{regular_user['id']}/restore", headers=admin_headers)
    assert restore_res.status_code == 200
    assert restore_res.get_json()["is_active"] is True

    fresh_login = api_client.post(
        "/api/login",
        json={"email": "regular@example.com", "password": "pwd123", "role": "user"},
    )
    assert fresh_login.status_code == 200
    fresh_headers = {"Authorization": f"Bearer {fresh_login.get_json()['session']['token']}"}

    reset_res = api_client.post(
        f"/api/admin/users/{regular_user['id']}/reset-password",
        headers=admin_headers,
        json={"new_password": "newpwd123"},
    )
    assert reset_res.status_code == 200
    assert "Password reset successfully" in reset_res.get_json()["message"]

    old_session = api_client.get("/api/me", headers=fresh_headers)
    assert old_session.status_code == 401

    new_login = api_client.post(
        "/api/login",
        json={"email": "regular@example.com", "password": "newpwd123", "role": "user"},
    )
    assert new_login.status_code == 200
    assert new_login.get_json()["email"] == "regular@example.com"


def test_admin_system_audit_views(api_client, session_factory):
    admin = api_client.post(
        "/api/register",
        json={"name": "System Admin", "email": "system.admin@unisplit.com", "password": "pwd123", "role": "admin"},
    ).get_json()
    creator = api_client.post(
        "/api/register",
        json={"name": "Creator", "email": "audit.creator@example.com", "password": "pwd123", "role": "user"},
    ).get_json()
    teammate = api_client.post(
        "/api/register",
        json={"name": "Teammate", "email": "audit.member@example.com", "password": "pwd123", "role": "user"},
    ).get_json()

    from backend.app.repositories.users import UserRepository
    db = session_factory()
    UserRepository(db).update_balance(teammate["id"], 50.00)
    db.close()

    group_res = api_client.post(
        "/api/groups",
        json={"name": "Audit Group", "description": "Audit test", "creator_id": creator["id"]},
    )
    assert group_res.status_code == 201
    group_id = group_res.get_json()["id"]

    member_res = api_client.post(
        f"/api/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {creator['session']['token']}"},
        json={"user_id": teammate["id"], "role": "MEMBER"},
    )
    assert member_res.status_code == 201

    expense_res = api_client.post(
        "/api/expenses",
        headers={"Authorization": f"Bearer {creator['session']['token']}"},
        json={
            "group_name": "Audit Group",
            "description": "Lunch",
            "amount": "25.00",
            "category": "Food",
            "payer_email": creator["email"],
            "participant_emails": [creator["email"], teammate["email"]],
        },
    )
    assert expense_res.status_code == 201
    expense_id = expense_res.get_json()["id"]

    settlement_res = api_client.post(
        f"/api/groups/{group_id}/settlements",
        headers={"Authorization": f"Bearer {teammate['session']['token']}"},
        json={
            "expense_id": expense_id,
            "payer_id": teammate["id"],
            "payee_id": creator["id"],
            "amount": "12.50",
            "note": "Lunch split",
        },
    )
    assert settlement_res.status_code == 201

    admin_headers = {"Authorization": f"Bearer {admin['session']['token']}"}
    transactions = api_client.get("/api/admin/system/transactions", headers=admin_headers)
    assert transactions.status_code == 200
    assert any(item["group_name"] == "Audit Group" for item in transactions.get_json()["transactions"])

    audit_logs = api_client.get("/api/admin/system/audit-logs", headers=admin_headers)
    assert audit_logs.status_code == 200
    assert any(item["action_type"] == "settlement_recorded" for item in audit_logs.get_json()["audit_logs"])

    denied = api_client.get("/api/admin/system/transactions", headers={"Authorization": f"Bearer {creator['session']['token']}"})
    assert denied.status_code == 403


def test_membership_routes_return_details(api_client, session_factory):
    user = api_client.post(
        "/api/register",
        json={"name": "Premium User", "email": "premium@example.com", "password": "pwd123", "role": "user"},
    ).get_json()

    from backend.app.repositories.users import UserRepository
    db = session_factory()
    UserRepository(db).update_balance(user["id"], 20.00)
    db.close()

    buy_res = api_client.post(
        "/api/membership/buy",
        headers={"Authorization": f"Bearer {user['session']['token']}"},
        json={"plan": "monthly"},
    )
    assert buy_res.status_code == 200
    buy_data = buy_res.get_json()
    assert buy_data["status"] == "success"
    assert buy_data["plan"] == "monthly"
    assert buy_data["is_vip"] is True
    assert buy_data["vip_expiry"] is not None
    assert buy_data["balance"] == pytest.approx(10.01, rel=1e-6)

def test_flask_serves_frontend_and_api_on_same_port(app_client):
    index = app_client.get("/")
    assert index.status_code == 200
    assert b"UniSplit" in index.data

    app_js = app_client.get("/js/app.js")
    assert app_js.status_code == 200
    assert b"API_BASE_URL" in app_js.data

    register = app_client.post(
        "/api/register",
        json={"name": "Static User", "email": "static@example.com", "password": "pwd123"},
    )
    assert register.status_code == 201
    assert register.get_json()["email"] == "static@example.com"
