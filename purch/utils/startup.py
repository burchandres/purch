import logging

from sqlmodel import create_engine, text

from purch.utils.config import get_settings

LOGGER = logging.getLogger(__name__)
settings = get_settings()


def init_db():
    LOGGER.debug("Initializing database...")
    server_engine_url = f"postgresql://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}"
    # Create the server engine to intialize the pirch db
    server_engine = create_engine(
        server_engine_url, echo=True, isolation_level="AUTOCOMMIT"
    )
    try:
        with server_engine.connect() as conn:
            # Create the database
            LOGGER.info(f"Creating database {settings.DB_NAME}")
            results = conn.execute(
                text(
                    f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{settings.DB_NAME}'"
                )
            )
            if results.fetchone() is not None:
                LOGGER.info(f"Database {settings.DB_NAME} already exists")
                return
            conn.execute(text(f"CREATE DATABASE {settings.DB_NAME}"))
            LOGGER.info(f"Database {settings.DB_NAME} created successfully")

    except Exception as e:
        LOGGER.error(f"Error initializing database: {e}")
        raise
