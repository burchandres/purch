from typing import Iterable

from sqlmodel import Session, select, delete

from purch.common.repository import AbstractPostgresRepository
from purch.domains.item.models import Item


class ItemRepository(AbstractPostgresRepository):
    def add(self, item: Item):
        with Session(self.engine) as session:
            session.add(item)
            session.commit()

    def add_all(self, items: Iterable[Item]):
        with Session(self.engine) as session:
            session.add_all(items)
            session.commit()

    def get(self, id: str) -> Item | None:
        with Session(self.engine) as session:
            statement = select(Item).where(Item.id == id)
            results = session.exec(statement)
            return results.first()

    def get_all(self) -> Iterable[Item]:
        with Session(self.engine) as session:
            statement = select(Item)
            results = session.exec(statement)
            return results.all()

    def delete(self, id: str):
        with Session(self.engine) as session:
            statement = delete(Item).where(Item.id == id)
            session.exec(statement)
            session.commit()