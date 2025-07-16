from abc import ABC
from sqlmodel import SQLModel, create_engine, Session
from typing import Any

from purch.domains.models import User, Category, Item, Account, Transaction
from purch.common.config import get_settings, Settings


class AbstractPostgresRepository(ABC):
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        engine_url = self.settings.get_postgres_url()
        self.engine = create_engine(engine_url, echo=True)
        SQLModel.metadata.create_all(self.engine)  # checkfirst=True by default

    def execute(self, statement: Any):
        with Session(self.engine) as session:
            session.exec(statement)
            session.commit()
