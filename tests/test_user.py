import uuid
import datetime as dt
import pytest

from fastapi import status

from purch.core.models import User
from purch.user.repository import UserRepository
from purch.infrastructure.auth.security import verify_password


AUTH_URL = "/auth"
REGISTER_URL = AUTH_URL + "/register"
LOGIN_URL = AUTH_URL + "/token"
USER_URL = "/user"
CURRENT_USER_URL = USER_URL + "/current"
DELETE_USER_URL = USER_URL + "/delete"

pytestmark = pytest.mark.anyio


def jsonify_user(user: User):
    json_user = user.model_dump()
    json_user["id"] = str(uuid.uuid4())
    json_user["salary"] = float(json_user["salary"])
    json_user["last_updated"] = dt.datetime.now(dt.timezone.utc).timestamp()
    return json_user


async def test_user_registration(configure_test_settings, test_client, test_user):
    test_settings = configure_test_settings
    # actual tests
    test_user = test_user
    response = await test_client.post(
        REGISTER_URL,
        json=test_user
    )
    # Check we get a 200 response
    assert response.status_code == status.HTTP_200_OK
    user_repository = UserRepository(settings=test_settings)
    registered_user = user_repository.get_via_username(test_user["username"])
    assert registered_user
    assert registered_user.username == test_user["username"]
    assert verify_password(test_user["password"], registered_user.password)


async def test_valid_user_login(configure_test_settings, test_client, test_user):
    """Test successful login with valid credentials using the OAuth2PasswordRequestForm format."""
    # Create a test user
    test_user = test_user
    
    # First register the user
    register_user_response = await test_client.post(
        REGISTER_URL, 
        json=test_user
    )
    # Check we get a 200 response
    assert register_user_response.status_code == status.HTTP_200_OK
    
    # Now hit the login endpoint with form data (mimicking OAuth2PasswordRequestForm)
    login_response = await test_client.post(
        LOGIN_URL,
        data={
            "username": test_user["username"],
            "password": test_user["password"],
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


async def test_invalid_password_login(configure_test_settings, test_client, test_user):
    """Test login failure with invalid password."""
    # Create and register a test user
    test_user = test_user
    
    register_user_response = await test_client.post(
        REGISTER_URL, 
        json=test_user
    )
    assert register_user_response.status_code == status.HTTP_200_OK
    
    # Try to login with incorrect password
    login_response = await test_client.post(
        LOGIN_URL,
        data={
            "username": test_user["username"],
            "password": "wrong_password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Check we get a 401 Unauthorized response
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_invalid_username_login(configure_test_settings, test_client):
    """Test login failure with non-existent username."""
    # Try to login with a username that doesn't exist
    login_response = await test_client.post(
        LOGIN_URL,
        data={
            "username": "nonexistent_user",
            "password": "any_password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Check we get a 401 Unauthorized response
    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_token_structure(configure_test_settings, test_db_name, test_client, test_user):
    """Test the structure and content of the token response."""
    # Create and register a test user
    test_user = test_user
    
    register_user_response = await test_client.post(
        REGISTER_URL, 
        json=test_user
    )
    assert register_user_response.status_code == status.HTTP_200_OK
    
    # Login to get token
    login_response = await test_client.post(
        LOGIN_URL,
        data={
            "username": test_user["username"],
            "password": test_user["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    
    # Check token structure
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    
    # Verify token can be used to access protected endpoints

############################################################
# Tests for protected endpoints are implemented below
############################################################


async def test_unauthenticated_access(configure_test_settings, test_db_name, test_client):
    """Test accessing protected endpoints without authentication fails."""
    # Try to access current user endpoint without a token
    current_user_response = await test_client.get(CURRENT_USER_URL)
    assert current_user_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Try to access delete user endpoint without a token
    delete_user_response = await test_client.delete(
        f"{DELETE_USER_URL}?id={uuid.uuid4()}"
    )
    assert delete_user_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_authenticated_current_user(configure_test_settings, test_db_name, test_client):
    """Test accessing current user endpoint with valid token returns correct user data."""
    # Register a user and get token
    test_user = await register_and_get_user(test_client)
    token = await get_auth_token(test_client, test_user)
    
    # Access current user endpoint with token
    current_user_response = await test_client.get(
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


async def test_delete_own_account(configure_test_settings, test_client):
    """Test deleting own account with valid token succeeds."""
    test_settings = configure_test_settings
    # Register a user and get token
    test_user = await register_and_get_user(test_client)
    test_user_id = UserRepository(settings=test_settings).get_via_username(username=test_user.username).id
    token = await get_auth_token(test_client, test_user)
    
    # Delete the user account
    delete_response = await test_client.delete(
        f"{DELETE_USER_URL}?id={test_user_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Verify successful deletion
    assert delete_response.status_code == status.HTTP_200_OK
    
    # Verify user can no longer access protected endpoints
    current_user_response = await test_client.get(
        CURRENT_USER_URL,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert current_user_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_delete_other_account(configure_test_settings, test_db_name, test_client):
    """Test attempting to delete another user's account fails with 401."""
    test_settings = configure_test_settings
    # Register first user
    test_user1 = await register_and_get_user(test_client)
    token1 = await get_auth_token(test_client, test_user1)
    
    # Create a second user with different username to avoid conflicts
    test_user2 = User(username="another.user", first_name="Another", last_name="User")
    json_test_user2 = jsonify_user(test_user2)
    
    # Register the second user
    register_response2 = await test_client.post(
        REGISTER_URL, 
        json=json_test_user2
    )
    assert register_response2.status_code == status.HTTP_200_OK
    registered_user2_id = UserRepository(settings=test_settings).get_via_username(username=test_user2.username).id
    
    # Try to delete the second user using the first user's token
    delete_response = await test_client.delete(
        f"{DELETE_USER_URL}?id={registered_user2_id}",
        headers={"Authorization": f"Bearer {token1}"}
    )
    
    # Verify deletion is not allowed
    assert delete_response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Verify second user still exists and can authenticate
    token2 = await get_auth_token(test_client, test_user2)
    current_user_response = await test_client.get(
        CURRENT_USER_URL,
        headers={"Authorization": f"Bearer {token2}"}
    )
    assert current_user_response.status_code == status.HTTP_200_OK
    assert current_user_response.json()["id"] == str(registered_user2_id)


async def test_invalid_token(configure_test_settings, test_client):
    """Test that an invalid token is rejected."""
    # Try to use an invalid token
    invalid_token = "invalid.token"
    current_user_response = await test_client.get(
        CURRENT_USER_URL,
        headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert current_user_response.status_code == status.HTTP_401_UNAUTHORIZED

############################################################
# Helper functions for protected endpoint tests
############################################################

async def get_auth_token(test_client, test_user):
    """Helper function to get an authentication token for a user."""
    login_response =  await test_client.post(
        LOGIN_URL,
        data={
            "username": test_user.username,
            "password": test_user.password,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == status.HTTP_200_OK
    return login_response.json()["access_token"]


async def register_and_get_user(test_client):
    """Helper function to register a user and return the user data."""
    test_user = User()
    json_test_user = jsonify_user(test_user)
    
    # Register the user
    register_response = await test_client.post(
        REGISTER_URL, 
        json=json_test_user
    )
    assert register_response.status_code == status.HTTP_200_OK
    
    return test_user
