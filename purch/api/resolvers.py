from ariadne import QueryType, ObjectType, load_schema_from_path, make_executable_schema
from ariadne.asgi import GraphQL

from purch.common.config import get_settings
from purch.domains.models import User, Item, Transaction, Account

from sqlmodel import SQLModel, create_engine, Session, select


settings = get_settings()
engine_url = settings.get_postgres_url()
engine = create_engine(engine_url, echo=True)
SQLModel.metadata.create_all(engine)

gql_schema = load_schema_from_path("purch/graphql/schema.graphql")

query = QueryType()
user = ObjectType("User")
item = ObjectType("Item")
transaction = ObjectType("Transaction")
account = ObjectType("Account")

# TODO: test these
# TODO: figure out how to resolve fields that are not directly on the db models

# USER RESOLUTION
@query.field("Users")
def resolve_users(*_):
    with Session(engine) as session:
        statement = select(User)
        results = session.exec(statement)
        return results.all()

@user.field("item")
def resolve_item(obj, _):
    with Session(engine) as session:
        statement = select(Item).where(Item.user_id == obj.user_id)
        results = session.exec(statement)
        return results.first()

@user.field("transactions")
def resolve_transaction(obj, _):
    with Session(engine) as session:
        statement = select(Transaction).where(Transaction.user_id == obj.user_id)
        results = session.exec(statement)
        return results.first()

# TRANSACTION RESOLUTION
@query.field("transactions")
def resolve_transactions(*, _):  # TODO: Need diff function name? Does decorator distinguish it?
    with Session(engine) as session:
        statement = select(Transaction)
        results = session.exec(statement)
        return results.all()

@transaction.field("account")
def resolve_account(obj, _):
    with Session(engine) as session:
        statement = select(Account).where(obj.account_id == Account.id)
        results = session.exec(statement)
        return results.first()

@transaction.field("user")
def resolve_user(obj, _):
    with Session(engine) as session:
        statement = select(User).where(obj.user_id == User.id)
        results = session.exec(statement)
        return results.first()

# ITEM RESOLUTION

# ACCOUNT RESOLUTION

schema = make_executable_schema(gql_schema, query)
app = GraphQL(schema, debug=True)
