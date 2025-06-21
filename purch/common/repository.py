from abc import ABC
from sqlmodel import SQLModel, create_engine, Session
from typing import Any

from purch.common.config import get_settings


class AbstractPostgresRepository(ABC):
    settings = get_settings()

    def __init__(self):
        engine_url = self.settings.get_postgres_url()
        self.engine = create_engine(engine_url, echo=True)
        SQLModel.metadata.create_all(self.engine)  # checkfirst=True by default

    def execute(self, statement: Any):
        with Session(self.engine) as session:
            session.exec(statement)
            session.commit()
