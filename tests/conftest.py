import pytest
import uuid
import datetime as dt

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from sqlmodel import create_engine, Session, text
from sqlalchemy.exc import OperationalError

from purch.main import app
from purch.common.config import Settings, get_settings
from purch.common.logger import get_logger
from purch.domains.models import User
from purch.domains.user.schemas import UserCreate
from purch.domains.user.service import UserService
from purch.infrastructure.auth.schemas import Token


logger = get_logger(__name__)

pytestmark = pytest.mark.anyio


def dict_to_user_class(user_dict: dict) -> User:
    user = User()
    user.__dict__ = user_dict
    return user


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_user():
    """Generate a test user in json form."""
    new_id = uuid.uuid4()
    test_user = User(
        id=new_id,
        username=f"user_{new_id.hex[:8]}",
        last_updated=dt.datetime.now(dt.timezone.utc).timestamp()
    )

    test_user_dict = test_user.model_dump()
    test_user_dict["income"] = float(test_user_dict["income"])
    test_user_dict["id"] = test_user_dict["id"].hex

    create_user = UserCreate(
        username=test_user.username,
        password=test_user.password,
        first_name=test_user.first_name,
        last_name=test_user.last_name
    )
    return test_user, test_user_dict, create_user


@pytest.fixture
def test_db_name():
    """Configure test db name upon import and return the name"""
    test_db_name = f"test_db_{uuid.uuid4().hex[:10]}"
    return test_db_name


@pytest.fixture
async def authenticated_test_client(test_user, configure_test_settings):
    from purch.infrastructure.auth.service import get_current_active_user
    from purch.api.routers.user import get_user_service
    from purch.common.dependencies import get_user_service
    from unittest.mock import Mock

    user, _, _ = test_user
    # patch the get_current_active_user dependency
    app.dependency_overrides[get_current_active_user] = lambda: user
    # patch the get_user_service dependency
    # this is to avoid trying to connect to database that hasn't been initialized yet
    test_settings = configure_test_settings

    def get_mocked_user_service():
        user_service = UserService(settings=test_settings)
        user_service.get_purch_jwt_access_token = Mock(
                return_value=Token(
                    access_token="valid-test-token",
                    token_type="bearer"
                )
            )
        return user_service

    app.dependency_overrides[get_user_service] = get_mocked_user_service

    async with LifespanManager(app):  # run lifespan (startup/shutdown)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def unauthenticated_test_client(configure_test_settings):
    from purch.api.routers.user import get_user_service

    # patch the get_user_service dependency
    test_settings = configure_test_settings
    # this is to avoid trying to connect to database that hasn't been initialized yet
    create_user_service = lambda: UserService(settings=test_settings)
    app.dependency_overrides[get_user_service] = create_user_service

    async with LifespanManager(app):  # run lifespan (startup/shutdown)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture
def configure_test_settings(request, monkeypatch, test_db_name):
    """
    Configure test database settings and ensure all modules use the test settings.

    This fixture:
    1. Clears the settings cache to ensure fresh settings
    2. Sets a unique POSTGRES_DATABASE environment variable
    3. Creates a new Settings instance with the test database name
    4. Patches all modules that use settings to use our test instance
    5. Yields the test_settings object for use in tests
    6. Cleans up the test database after test completion
    """
    # Clear the cached settings to ensure we get a fresh instance
    get_settings.cache_clear()

    # Set the environment variable
    test_db_name = test_db_name
    monkeypatch.setenv("POSTGRES_DATABASE", test_db_name)
    monkeypatch.setenv("POSTGRES_HOST", "test-postgres")
    monkeypatch.setenv("REDIS_HOST", "test-redis")

    # Create new settings instance (will pick up the environment variables)
    test_settings = Settings()

    # Ensure all modules use our test settings
    modules_to_patch = [
        "purch.api.startup.get_settings",
        "purch.api.routers.user.get_settings",
        "purch.common.repository.get_settings",
        "purch.infrastructure.auth.service.get_settings",
        "purch.infrastructure.plaid.tokens.get_settings",
        "purch.infrastructure.plaid.client.get_settings",
        "purch.infrastructure.taskiq.get_settings",
        "purch.infrastructure.taskiq.tasks.get_settings",
        "purch.domains.user.service.get_settings",
    ]

    # Use lambda to ensure the same instance is returned each time
    for module in modules_to_patch:
        monkeypatch.setattr(module, lambda: test_settings)

    # The taskiq module will automatically use InMemoryBroker for tests
    # based on the test database name pattern

    yield test_settings  # Yield the settings in case tests need to access it

    # Check if test passed and clean up accordingly
    if hasattr(request.node, 'rep_call') and request.node.rep_call.passed:
        try:
            teardown_test_db(test_db_name=test_settings.POSTGRES_DATABASE, test_settings=test_settings)
        except OperationalError as e:
            logger.warning(f"Could not clean up test database {test_settings.POSTGRES_DATABASE}: {str(e)}")
    else:
        logger.info(f"Test failed -- data preserved in db: {test_settings.POSTGRES_DATABASE}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # Set a report attribute for each phase of a call
    setattr(item, f"rep_{rep.when}", rep)


def teardown_test_db(test_db_name: str, test_settings: Settings):
    """Attempt to clean up the test database. Logs warning if unsuccessful."""
    # Use test settings to get the correct database connection
    db_uri = f"postgresql://{test_settings.POSTGRES_USERNAME}:{test_settings.POSTGRES_PASSWORD.get_secret_value()}@{test_settings.POSTGRES_HOST}:{test_settings.POSTGRES_PORT}"
    admin_engine = create_engine(db_uri, isolation_level="AUTOCOMMIT")
    try:
        with Session(admin_engine) as session:
            session.exec(text(f"DROP DATABASE IF EXISTS {test_db_name}"))
            session.commit()
        logger.debug(f"Successfully cleaned up test database {test_db_name}")
    except Exception as e:
        logger.warning(f"Failed to clean up test database {test_db_name}: {str(e)}")
        raise
