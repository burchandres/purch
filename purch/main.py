from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from purch.infrastructure.taskiq import broker
from purch.api.routers import (
    user_router,
    budget_router,
)
from purch.utils.project_version import version
from purch.api.startup import init_db
from purch.common.logger import get_logger


logger = get_logger(__name__)


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
    if not broker.is_worker_process:
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
    prefix="/users",
    tags=["users"],
)
# Add core finance service for plaid integration
app.include_router(
    router=budget_router,
    prefix="/budget",
    tags=["budget"],
)


@app.get("/")
def main():
    return {
        "service": "Purch",
        "version": str(version).strip(),
    }
