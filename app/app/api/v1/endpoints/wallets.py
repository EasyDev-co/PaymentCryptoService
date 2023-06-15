from typing import List

from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide

from app.api.deps import commit_and_close_session, get_current_user
from app.core.containers import Container

from app.schemas.wallets import WalletCryptocurrencyOut, WalletGetData

from app.services.wallet import WalletService

router = APIRouter()


@router.get('/list', response_model=List[WalletCryptocurrencyOut])
@inject
@commit_and_close_session
async def list_wallets(
        user_id: str,
        # user_id=Depends(get_current_user)
        wallet_service: WalletService = Depends(Provide[Container.wallet_service])
):
    return await wallet_service.get_wallets(user_id=user_id)


@router.get('/get/{wallet_id}', response_model=WalletGetData)
@inject
@commit_and_close_session
async def get_wallet(
        user_id: str,
        wallet_id: str,
        # user_id=Depends(get_current_user)
        wallet_service: WalletService = Depends(Provide[Container.wallet_service])
):
    return await wallet_service.get_wallet(
        user_id=user_id,
        wallet_id=wallet_id
    )
