from abc import ABC, abstractmethod
from sqlmodel import SQLModel, create_engine, Session
from typing import Any

from purch.core.models import User, Item, Account, Transaction
from purch.utils.config import get_settings

settings = get_settings()


class AbstractRepository(ABC):
    db_type_default = "postgresql"

    def __init__(self):
        engine_url = f"{self.db_type_default}://{settings.DB_USERNAME}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
        self.engine = create_engine(engine_url, echo=True)
        SQLModel.metadata.create_all(self.engine)  # checkfirst=True by default

    @abstractmethod
    def add(self, object: Any):
        pass

    @abstractmethod
    def delete(self, object: Any):
        pass

    def execute(self, statement: Any):
        with Session(self.engine) as session:
            session.exec(statement)
            session.commit()
