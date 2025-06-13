import taskiq_fastapi

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from purch.core import broker
from purch.user.router import router as user_router
from purch.auth.router import router as auth_router
from purch.finance.router import router as finance_router
from purch.utils.project_version import version
from purch.core.startup import init_db
from purch.utils.logger import get_logger


LOGGER = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup code here

    # Start up the database
    init_db()
    # Start up our taskiq broker
    if not broker.is_worker_process:
        await broker.startup()

    yield
    # Shutdown code here

    # shutdown taskiq broker
    if broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(
    title="Purch",
    description="Purch is a personal financial management service to help manage the everyday and big picture financials of your life.",
    version=str(version).strip(),
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add user service
app.include_router(
    router=user_router,
    prefix="/user",
    tags=["user"],
)
# Add auth service
app.include_router(
    router=auth_router,
    prefix="/auth",
    tags=["auth"],
)
# Add core finance service for plaid integration
app.include_router(
    router=finance_router,
    prefix="/finance",
    tags=["finance"],
)

taskiq_fastapi.init(broker, app)


@app.get("/")
def main():
    return {
        "service": "Purch",
        "version": str(version).strip(),
    }
