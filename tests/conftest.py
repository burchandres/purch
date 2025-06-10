import pytest
import uuid
import datetime as dt

from sqlmodel import create_engine, Session, text
from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient

from purch.main import app
from purch.utils.config import Settings, get_settings
from purch.utils.logger import get_logger
from purch.core.models import User


LOGGER = get_logger(__name__)


def dict_to_user_class(user_dict: dict) -> User:
    user = User()
    user.__dict__ = user_dict
    return user

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
def configure_test_settings(request, monkeypatch, test_db_name):
    """
    Configure test database settings and ensure all modules use the test settings.
    
    This fixture:
    1. Clears the settings cache to ensure fresh settings
    2. Sets a unique DB_NAME environment variable 
    3. Creates a new Settings instance with the test database name
    4. Patches all modules that use settings to use our test instance
    5. Yields the test_settings object for use in tests
    6. Cleans up the test database after test completion
    """
    # Clear the cached settings to ensure we get a fresh instance
    get_settings.cache_clear()
    
    # Set the environment variable
    test_db_name = test_db_name
    monkeypatch.setenv("DB_NAME", test_db_name)
    monkeypatch.setenv("DB_HOST", "localhost")
    
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
        "purch.finance.router.get_settings"
    ]
    
    # Use lambda to ensure the same instance is returned each time
    for module in modules_to_patch:
        monkeypatch.setattr(module, lambda: test_settings)

    yield test_settings  # Yield the settings in case tests need to access it

    # Check if test passed and clean up accordingly
    if hasattr(request.node, 'rep_call') and request.node.rep_call.passed:
        try:
            teardown_test_db(test_db_name=test_settings.DB_NAME)
        except OperationalError as e:
            LOGGER.warning(f"Could not clean up test database {test_settings.DB_NAME}: {str(e)}")
    else:
        LOGGER.info(f"Test failed -- data preserved in db: {test_settings.DB_NAME}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # Set a report attribute for each phase of a call
    setattr(item, f"rep_{rep.when}", rep)


def teardown_test_db(test_db_name: str):
    """Attempt to clean up the test database. Logs warning if unsuccessful."""
    db_uri = f"postgresql://postgres:password@localhost:5432"
    admin_engine = create_engine(db_uri, isolation_level="AUTOCOMMIT")
    try:
        with Session(admin_engine) as session:
            session.exec(text(f"DROP DATABASE {test_db_name}"))
            session.commit()
        LOGGER.debug(f"Successfully cleaned up test database {test_db_name}")
    except Exception as e:
        LOGGER.warning(f"Failed to clean up test database {test_db_name}: {str(e)}")
        raise


@pytest.fixture
def configure_get_current_active_user(test_user):
    from purch.auth.security import get_current_active_user
    
    # Clear any existing overrides
    app.dependency_overrides = {}
    user = dict_to_user_class(test_user)
    app.dependency_overrides[get_current_active_user] = lambda: user


@pytest.fixture
def test_client(configure_test_settings):
    """
    Create a test client with proper database initialization.
    
    This fixture ensures that:
    1. Test settings are in place before any database operations
    2. The test database is created before the application starts
    3. The application uses the test database throughout the test
    """
    # Create and yield the test client
    app.dependency_overrides = {}
    with TestClient(app) as client:
        yield client
