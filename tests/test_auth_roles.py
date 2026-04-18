import pytest

def test_admin_and_user_creation_roles(api_client):
    """
    Test that users are assigned correct roles based on their email domain.
    """
    # 1. Regular user registration
    resp_user = api_client.post(
        "/api/register",
        json={"name": "Regular User", "email": "user@example.com", "password": "password123", "role": "user"},
    )
    assert resp_user.status_code == 201
    data_user = resp_user.get_json()
    assert data_user["is_admin"] is False
    assert data_user["role"] == "user"

    # 2. Admin user registration
    resp_admin = api_client.post(
        "/api/register",
        json={"name": "Admin User", "email": "admin@unisplit.com", "password": "password123", "role": "admin"},
    )
    assert resp_admin.status_code == 201
    data_admin = resp_admin.get_json()
    assert data_admin["is_admin"] is True
    assert data_admin["role"] == "admin"


def test_explicit_admin_registration_and_login_role_checks(api_client):
    admin_register = api_client.post(
        "/api/register",
        json={"name": "Explicit Admin", "email": "explicit@unisplit.com", "password": "password123", "role": "admin"},
    )
    assert admin_register.status_code == 201
    admin_data = admin_register.get_json()
    assert admin_data["is_admin"] is True

    invalid_admin_register = api_client.post(
        "/api/register",
        json={"name": "Wrong Admin", "email": "wrong@example.com", "password": "password123", "role": "admin"},
    )
    assert invalid_admin_register.status_code == 400

    normal_login = api_client.post(
        "/api/login",
        json={"email": "explicit@unisplit.com", "password": "password123", "role": "user"},
    )
    assert normal_login.status_code == 200

    admin_login = api_client.post(
        "/api/login",
        json={"email": "explicit@unisplit.com", "password": "password123", "role": "admin"},
    )
    assert admin_login.status_code == 200

    denied_admin_login = api_client.post(
        "/api/register",
        json={"name": "Normal User", "email": "normal@example.com", "password": "password123"},
    ).get_json()
    denied_login = api_client.post(
        "/api/login",
        json={"email": denied_admin_login["email"], "password": "password123", "role": "admin"},
    )
    assert denied_login.status_code == 403


def test_expense_visibility_isolation(api_client):
    """
    Verify that:
    - User A can see their own expenses.
    - User B (not involved) cannot see User A's expenses.
    - Admin C can see everything.
    """
    # 1. Setup users
    user_a = api_client.post(
        "/api/register",
        json={"name": "User A", "email": "a@example.com", "password": "password123"},
    ).get_json()
    token_a = user_a["session"]["token"]

    user_b = api_client.post(
        "/api/register",
        json={"name": "User B", "email": "b@example.com", "password": "password123"},
    ).get_json()
    token_b = user_b["session"]["token"]

    admin_c = api_client.post(
        "/api/register",
        json={"name": "Admin C", "email": "admin_c@unisplit.com", "password": "password123"},
    ).get_json()
    token_c = admin_c["session"]["token"]

    # 2. User A creates an expense (not involving B)
    expense_res = api_client.post(
        "/api/expenses",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "group_name": "Personal Trip",
            "description": "Coffee",
            "amount": "5.50",
            "category": "Food",
            "payer_email": "a@example.com",
            "participant_emails": ["a@example.com"], # Only A is involved
        },
    )
    assert expense_res.status_code == 201

    # 3. Check Visibility for User A
    history_a = api_client.get(
        "/api/expenses",
        headers={"Authorization": f"Bearer {token_a}"},
    ).get_json()
    assert len(history_a["expenses"]) == 1
    assert history_a["expenses"][0]["description"] == "Coffee"

    # 4. Check Visibility for User B (Should be empty because B is not the payer nor a participant)
    history_b = api_client.get(
        "/api/expenses",
        headers={"Authorization": f"Bearer {token_b}"},
    ).get_json()
    assert len(history_b["expenses"]) == 0

    # 5. Check Visibility for Admin C (Should see User A's expense)
    history_c = api_client.get(
        "/api/expenses",
        headers={"Authorization": f"Bearer {token_c}"},
    ).get_json()
    assert len(history_c["expenses"]) == 1
    assert history_c["expenses"][0]["description"] == "Coffee"
    assert history_c["expenses"][0]["payer"] == "User A"

    # 6. User A can search by email as well as description.
    history_email = api_client.get(
        "/api/expenses?search=a@example.com",
        headers={"Authorization": f"Bearer {token_a}"},
    ).get_json()
    assert len(history_email["expenses"]) == 1
