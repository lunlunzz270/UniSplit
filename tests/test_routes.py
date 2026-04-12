def test_auth_and_expense_routes(api_client):
    register = api_client.post(
        "/api/register",
        json={"name": "Route User", "email": "route@example.com", "password": "pwd123"},
    )
    assert register.status_code == 201
    assert register.get_json()["email"] == "route@example.com"

    login = api_client.post(
        "/api/login",
        json={"email": "route@example.com", "password": "pwd123"},
    )
    assert login.status_code == 200
    assert login.get_json()["name"] == "Route User"

    teammate = api_client.post(
        "/api/register",
        json={"name": "Teammate", "email": "team@example.com", "password": "pwd123"},
    ).get_json()

    expense = api_client.post(
        "/api/expenses",
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
