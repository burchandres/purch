import pytest
import uuid
import datetime as dt
import decimal

from fastapi import status

from purch.core.models import User
from purch.user.repository import UserRepository
from purch.auth.security import verify_password

# TODO: implement user related tests...
#       ...user registration
#       ...verifying registration
#       ...attempting to login with correct and incorrect passwords

AUTH_URL = "/auth"
REGISTER_URL = AUTH_URL + "/register"
LOGIN_URL = AUTH_URL + "/login"


def jsonify_user(user: User):
    json_user = user.model_dump()
    json_user["id"] = str(uuid.uuid4())
    json_user["salary"] = float(json_user["salary"])
    return json_user


def test_user_registration(configure_test_settings, test_db_name, test_client):
    test_settings = configure_test_settings
    # make sure the settings are correct
    assert test_settings.DB_HOST == "localhost"
    assert test_settings.DB_NAME == test_db_name
    # actualy tests
    test_user = User()
    json_test_user = jsonify_user(test_user)
    response = test_client.post(
        REGISTER_URL,
        json=json_test_user
    )
    # Check we get a 200 response
    assert response.status_code == status.HTTP_200_OK
    user_repository = UserRepository(settings=test_settings)
    registered_user = user_repository.get_via_username(test_user.username)
    assert registered_user
    assert registered_user.username == test_user.username
    assert verify_password(test_user.password, registered_user.password)

# def test_valid_user_login(test_db_name, test_client):
#     test_user = User()
#     # first register
#     register_user_response = test_client.post(REGISTER_URL, data=test_user)
#     # check we get a 200 response
#     assert register_user_response.status_code == status.HTTP_200_OK
#     # now hit the login endpoint
#     login_response = test_client.post(LOGIN_URL, data=test_user)
#     assert login_response.status_code == status.HTTP_200_OK
#     token = login_response.json().get("access_token", None)
#     assert token is not None

# def test_invalid_user_login(test_db_name, test_client):
#     test_user = User()
#     # register user
#     register_user_response = test_client.post(REGISTER_URL, data=test_user)
#     # check we get a 200 response
#     assert register_user_response.status_code == status.HTTP_200_OK
#     # hit login endpoint with different user that isn't registered
#     different_test_user = User(
#         first_name="foo", 
#         last_name="bar",
#         username="foo.bar",
#     )
#     invalid_login_response = test_client.post(LOGIN_URL, data=different_test_user)
#     # check we get 401 response
#     assert invalid_login_response.status_code == status.HTTP_401_UNAUTHORIZED
        