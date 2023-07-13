from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from app.api.deps import commit_and_close_session, get_current_user

from app.core.containers import Container

from app.services.transaction_service import CryptoTransactionService

router = APIRouter()


@router.get('/list')
@inject
@commit_and_close_session
async def list_transactions(
        # user_id: str,
        user_id=Depends(get_current_user),
        transactions_service: CryptoTransactionService = Depends(Provide[Container.crypto_transaction_service])
):
    return await transactions_service.list(user_id=user_id)


@router.get('/get/{transaction_id}')
@inject
@commit_and_close_session
async def get_transaction(
        transaction_id: str,
        user_id=Depends(get_current_user),
        transaction_service: CryptoTransactionService = Depends(Provide[Container.crypto_transaction_service])
):
    return await transaction_service.get(transaction_id=transaction_id)
