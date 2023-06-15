from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.api import deps
from app.api.v1 import api

from app.api.v1.endpoints import (
    webhook,
    users,
    wallets,
    transactions
)

from app.core.config import settings
from app.core.containers import Container
from app.exceptions.base import (
    BaseNotFound,
    YouHaveNoRights
)


def create_app():
    container = Container()
    container.wire(
        modules=[deps, api, users,
                 wallets, transactions, webhook]
    )
    fastapi_app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    fastapi_app.container = container

    fastapi_app.include_router(api.api_router, prefix=settings.API_V1_STR)
    return fastapi_app


app = create_app()


@app.exception_handler(BaseNotFound)
async def custom_http_exception_handler(request, exc):
    print(exc)
    return Response(status_code=404, content=str(exc))


@app.exception_handler(YouHaveNoRights)
async def custom_http_exception_handler(request, exc):
    print(exc)
    return Response(status_code=403, content=str(exc))
