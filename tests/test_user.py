import pytest
import datetime as dt

from fastapi import status

from purch.domains.user.repository import UserRepository
from purch.domains.user.schemas import UserUpdate
from purch.infrastructure.auth.service import verify_password, create_purch_jwt_access_token


BASE_USER_URL = "/users"
CURRENT_USER_URL = BASE_USER_URL + "/current"
TOKEN_URL = BASE_USER_URL + "/token"
REGISTER_URL = BASE_USER_URL + "/register"
DELETE_USER_URL = BASE_USER_URL + "/delete"
UPDATE_USER_URL = BASE_USER_URL + "/update"


async def test_user_registration(configure_test_settings, unauthenticated_test_client, test_user):
    test_settings = configure_test_settings
    # register a test user
    user, _, create_user = test_user
    response = await unauthenticated_test_client.post(
        REGISTER_URL,
        json=create_user.model_dump()
    )
    user_repository = UserRepository(settings=test_settings)
    # Check we get a 200 response
    assert response.status_code == status.HTTP_200_OK
    registered_user = user_repository.get_user_by_username(user.username)
    assert registered_user
    assert create_user.username == user.username
    assert registered_user.username == create_user.username
    assert user.password == create_user.password
    assert verify_password(create_user.password, registered_user.password)


async def test_user_update(configure_test_settings, authenticated_test_client, test_user):
    # register a test user
    user, _, _ = test_user

    # update the user
    user_update = UserUpdate(
        first_name="Bofa",
        last_name="Grover"
    )
    update_response = await authenticated_test_client.patch(
        UPDATE_USER_URL,
        json=user_update.model_dump()
    )
    assert update_response.status_code == status.HTTP_200_OK
    # check that the returned UserResponse has the fields we want changed changed
    update_response = update_response.json()
    assert user.id == update_response["id"]
    assert update_response["first_name"] == "Bofa"
    assert update_response["last_name"] == "Grover"
    assert update_response["income"] == user.income
    assert update_response["income_rate"] == user.income_rate

# TODO: figure out why this is failing
@pytest.mark.skip
async def test_valid_user_login(configure_test_settings, authenticated_test_client, test_user):
    """Test successful login with valid credentials using the OAuth2PasswordRequestForm format."""
    # Create a test user
    user, _, _ = test_user

    # Now hit the login endpoint with form data (mimicking OAuth2PasswordRequestForm)
    login_response = await authenticated_test_client.post(
        TOKEN_URL,
        data={
            "username": user.username,
            "password": user.password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Check response status and content
    assert login_response.status_code == status.HTTP_200_OK
    response_data = login_response.json()

    # Verify token structure
    assert "access_token" in response_data
    assert "token_type" in response_data
    assert response_data["token_type"] == "bearer"
    assert response_data["access_token"] is not None


async def test_invalid_password_login(configure_test_settings, unauthenticated_test_client, test_user):
    """Test login failure with invalid password."""
    # Create and register a test user
    test_user, _, _ = test_user

    # Try to login with incorrect password
    login_response = await unauthenticated_test_client.post(
        TOKEN_URL,
        data={
            "username": test_user.username,
            "password": "wrong_password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Check we get a 401 Unauthorized response
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_invalid_username_login(configure_test_settings, unauthenticated_test_client):
    """Test login failure with non-existent username."""
    # Try to login with a username that doesn't exist
    login_response = await unauthenticated_test_client.post(
        TOKEN_URL,
        data={
            "username": "nonexistent_user",
            "password": "any_password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    # Check we get a 401 Unauthorized response
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


############################################################
# Tests for protected endpoints are implemented below
############################################################


async def test_unauthenticated_access(configure_test_settings, unauthenticated_test_client):
    """Test accessing protected endpoints without authentication fails."""
    # Try to access current user endpoint without a token
    current_user_response = await unauthenticated_test_client.get(CURRENT_USER_URL)
    assert current_user_response.status_code == status.HTTP_401_UNAUTHORIZED

    # Try to access delete user endpoint without a token
    delete_user_response = await unauthenticated_test_client.delete(DELETE_USER_URL)
    assert delete_user_response.status_code == status.HTTP_401_UNAUTHORIZED


# TODO: figure out way this is failing...
@pytest.mark.skip
async def test_authenticated_current_user(configure_test_settings, unauthenticated_test_client, test_user):
    """Test accessing current user endpoint with valid token returns correct user data."""
    test_settings = configure_test_settings
    # Register a user and get token
    test_user, _, create_user = test_user
    register_response = await unauthenticated_test_client.post(
        REGISTER_URL,
        data=create_user.model_dump()
    )
    assert register_response.status_code == status.HTTP_200_OK
    # get token
    token = get_auth_token(test_user, test_settings)

    # Access current user endpoint with token
    current_user_response = await unauthenticated_test_client.get(
        CURRENT_USER_URL,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify response
    assert current_user_response.status_code == status.HTTP_200_OK
    current_user_data = current_user_response.json()

    # Verify user data matches
    assert current_user_data["username"] == test_user.username
    assert current_user_data["first_name"] == test_user.first_name
    assert current_user_data["last_name"] == test_user.last_name

# TODO: figure out why this is failing...
@pytest.mark.skip
async def test_delete_own_account(configure_test_settings, unauthenticated_test_client, test_user):
    """Test deleting own account with valid token succeeds."""
    test_settings = configure_test_settings
    # Register a user and get token
    test_user, _, user_create = test_user
    register_response = await unauthenticated_test_client.post(
        REGISTER_URL,
        data=user_create.model_dump()
    )
    assert register_response.status_code == status.HTTP_200_OK
    # get token
    token = get_auth_token(test_user, test_settings)

    # Delete the user account
    delete_response = await unauthenticated_test_client.delete(
        DELETE_USER_URL,
        headers={"Authorization": f"Bearer {token}"}
    )

    # Verify successful deletion
    assert delete_response.status_code == status.HTTP_200_OK

    # Verify user can no longer access protected endpoints
    current_user_response = await unauthenticated_test_client.get(
        CURRENT_USER_URL,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert current_user_response.status_code == status.HTTP_401_UNAUTHORIZED

############################################################
# Helper functions for protected endpoint tests
############################################################

def get_auth_token(test_user, test_settings) -> str:
    """Helper function to get an authentication token for a user."""
    token_expiration = dt.timedelta(minutes=5)
    auth_token = create_purch_jwt_access_token(
        data={"sub": str(test_user.id)},
        settings=test_settings,
        expires_delta=token_expiration
    )
    return auth_token
