from abc import ABC, abstractmethod
from sqlmodel import SQLModel, create_engine, Session
from typing import Any, Iterable, Optional

from purch.common.config import Settings


class AbstractPostgresRepository(ABC):
    def __init__(self, settings: Settings):
        engine_url = settings.get_postgres_url()
        self.engine = create_engine(engine_url, echo=True)
        SQLModel.metadata.create_all(self.engine)  # checkfirst=True by default

    @abstractmethod
    def add(self, object: Any):
        pass

    @abstractmethod
    def add_all(self, objects: Iterable[Any]):
        pass

    @abstractmethod
    def get_all(self, object_type: Optional[str]):
        pass

    @abstractmethod
    def delete(self, object: Any):
        pass

    def execute(self, statement: Any):
        with Session(self.engine) as session:
            session.exec(statement)
            session.commit()
