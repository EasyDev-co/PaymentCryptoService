from fastapi import APIRouter
from app.api.v1.endpoints import (
    transactions,
    users,
    wallets,
    webhook
)

api_router = APIRouter()

api_router.include_router(users.router, prefix='/users', tags=['users'])
api_router.include_router(wallets.router, prefix='/wallets', tags=['wallets'])
api_router.include_router(transactions.router, prefix='/transactions', tags=['transactions'])
api_router.include_router(webhook.router, prefix='/webhook', tags=['webhook'])
