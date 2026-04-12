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

    history = api_client.get("/api/expenses")
    assert history.status_code == 200
    records = history.get_json()["expenses"]
    assert len(records) == 1
    assert records[0]["group_name"] == "Sprint 5 Trip"

    logout = api_client.post(
        "/api/logout",
        json={"session_token": session_token},
    )
    assert logout.status_code == 200

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


def test_group_settlement_and_activity_log_routes(api_client):
    creator = api_client.post(
        "/api/register",
        json={"name": "Creator", "email": "creator@example.com", "password": "pwd123"},
    ).get_json()
    teammate = api_client.post(
        "/api/register",
        json={"name": "Teammate", "email": "teammate@example.com", "password": "pwd123"},
    ).get_json()

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

    settlement_res = api_client.post(
        f"/api/groups/{group_id}/settlements",
        json={
            "payer_id": teammate["id"],
            "payee_id": creator["id"],
            "amount": "12.50",
            "note": "Lunch split",
        },
    )
    assert settlement_res.status_code == 201
    assert settlement_res.get_json()["amount"] == 12.5

    logs = api_client.get(f"/api/groups/{group_id}/activity-logs")
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
