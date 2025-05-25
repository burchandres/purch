import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pirch.user.router import router as user_router
from pirch.auth.router import router as auth_router
from pirch.financial.router import router as finance_router
from pirch.utils.project_version import version
from pirch.utils.startup import init_db


LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup code here
    init_db()
    yield
    # Shutdown code here


app = FastAPI(
    title="Pirch",
    description="Pirch is a personal financial management service to help manage the everyday and big picture financials of your life.",
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
app.include_router(router=finance_router, prefix="/plaid", tags=["finance", "plaid"])


@app.get("/")
def main():
    return {
        "service": "Pirch",
        "version": str(version).strip(),
    }
