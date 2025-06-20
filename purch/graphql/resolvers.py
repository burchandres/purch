from ariadne import gql, QueryType, ObjectType, load_schema_from_path
from purch.api.routers.user import get_user_repository
from purch.domains.finance.repository import FinanceRepository
from purch.domains.user.repository import UserRepository

schema = load_schema_from_path("purch/graphql/schema.graphql")

query = QueryType()
user_repository = UserRepository()
finance_repository = FinanceRepository()

# TODO: test these
# USER RESOLUTION
@query.field("Users")
def resolve_users(*_):
    return user_repository.get_all()

user = ObjectType("User")

@user.field("item")
def resolve_items(obj, _):
    # TODO: add get item by user id to finance repository
    # finance_repository.get(obj)
    return

@user.field("transactions")
def resolve_transactions(obj, _):
    # TODO: add get transaction by user id to finance repository
    return

# TRANSACTION RESOLUTION

