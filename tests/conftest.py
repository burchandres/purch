import pytest
import uuid
import datetime as dt

from httpx import AsyncClient, ASGITransport
from asgi_lifespan import LifespanManager
from sqlmodel import create_engine, Session, text
from sqlalchemy.exc import OperationalError

from purch.main import app
from purch.utils.config import Settings, get_settings
from purch.utils.logger import get_logger
from purch.core.models import User


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
    test_user = User(
        id=uuid.uuid4(),
        last_updated=dt.datetime.now(dt.timezone.utc).timestamp()
    )
    test_user = test_user.model_dump()
    test_user["salary"] = float(test_user["salary"])
    test_user["id"] = test_user["id"].hex
    return test_user


@pytest.fixture
def test_db_name():
    """Configure test db name upon import and return the name"""
    test_db_name = f"test_db_{uuid.uuid4().hex[:10]}"
    return test_db_name


@pytest.fixture
def configure_get_current_active_user(test_user):
    from purch.auth.security import get_current_active_user
    
    # Clear any existing overrides
    app.dependency_overrides = {}
    user = dict_to_user_class(test_user)
    app.dependency_overrides[get_current_active_user] = lambda: user


@pytest.fixture(scope="function")
async def test_client():
    app.dependency_overrides = {}
    async with LifespanManager(app):  # run lifespan (startup/shutdown)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


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
        "purch.core.startup.get_settings", 
        "purch.auth.router.get_settings",
        "purch.auth.security.get_settings",
        "purch.finance.plaid.get_settings",
        "purch.finance.tokens.get_settings",
        "purch.user.router.get_settings",
        "purch.finance.router.get_settings",
        "purch.core.taskiq.get_settings",
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
