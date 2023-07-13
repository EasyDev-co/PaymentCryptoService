from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from dependency_injector.wiring import inject, Provide

from jose import jwt, JWTError

from functools import wraps
from uuid import uuid4


from app.core.containers import Container
from app.core.config import settings
from app.db.session import scope, SyncSession
from app.utils import errors_const


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@inject
async def get_current_user(token: str = Depends(oauth2_scheme)):
    algorithm = 'HS256'
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[algorithm])
        user_uuid = payload.get("user_uuid")
        if user_uuid is None:
            raise credentials_exception
        return user_uuid
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=errors_const.CREDENTIALS_ERROR,
        )


@inject
def commit_and_close_session(func):
    @wraps(func)
    @inject
    async def wrapper(db: SyncSession = Depends(Provide[Container.db]), *args, **kwargs,):
        scope.set(str(uuid4()))
        try:
            result = await func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            raise e
        finally:
            # db.session.expunge_all()
            db.scoped_session.remove()

    return wrapper
