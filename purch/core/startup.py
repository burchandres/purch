from sqlmodel import create_engine, text

from purch.utils.config import get_settings
from purch.utils.logger import get_logger

LOGGER = get_logger(__name__)


def init_db():
    LOGGER.debug("Initializing database...")
    settings = get_settings()  # Move settings initialization here for testing
    server_engine_url = f"postgresql://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD.get_secret_value()}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}"
    # Create the server engine to intialize the settings.POSTGRES_DATABASE db
    server_engine = create_engine(
        server_engine_url, echo=True, isolation_level="AUTOCOMMIT"
    )
    try:
        with server_engine.connect() as conn:
            # Create the database
            LOGGER.info(f"Creating database {settings.POSTGRES_DATABASE}")
            results = conn.execute(
                text(
                    f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{settings.POSTGRES_DATABASE}'"
                )
            )
            if results.fetchone() is not None:
                LOGGER.info(f"Database {settings.POSTGRES_DATABASE} already exists")
                return
            conn.execute(text(f"CREATE DATABASE {settings.POSTGRES_DATABASE}"))
            LOGGER.info(f"Database {settings.POSTGRES_DATABASE} created successfully")

    except Exception as e:
        LOGGER.error(f"Error initializing database: {e}")
        raise
