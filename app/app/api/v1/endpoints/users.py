from fastapi import APIRouter, Depends, Response
from dependency_injector.wiring import inject, Provide

from app.api.deps import commit_and_close_session, get_current_user

from app.core.containers import Container

from app.repository.user import RepositoryUser

from app.services.wallet import WalletService


router = APIRouter()


@router.post('/create')
@inject
@commit_and_close_session
async def create_user(
        # user_id: int,
        user_id=Depends(get_current_user),
        repository_user: RepositoryUser = Depends(Provide[Container.repository_user]),
        wallet_service: WalletService = Depends(Provide[Container.wallet_service])
):
    user = repository_user.create(
        obj_in={
            "user_id": user_id
        }
    )
    await wallet_service.create_all_wallets(user_id=user.id)
    return Response(status_code=200, content="User created")
