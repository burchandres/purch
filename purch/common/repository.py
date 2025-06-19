import uuid

from abc import ABC, abstractmethod
from sqlmodel import SQLModel, create_engine, Session
from typing import Any, Iterable

from purch.common.config import get_settings


class AbstractPostgresRepository(ABC):
    settings = get_settings()
    
    def __init__(self):
        engine_url = self.settings.get_postgres_url()
        self.engine = create_engine(engine_url, echo=True)
        SQLModel.metadata.create_all(self.engine)  # checkfirst=True by default

    @abstractmethod
    def add(self, object: Any):
        pass

    @abstractmethod
    def add_all(self, objects: Iterable[Any]):
        pass

    @abstractmethod
    def get(self, id: str | uuid.UUID):
        pass

    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def delete(self, object: Any):
        pass

    def execute(self, statement: Any):
        with Session(self.engine) as session:
            session.exec(statement)
            session.commit()
