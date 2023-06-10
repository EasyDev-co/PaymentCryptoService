from fastapi import Header, Depends, HTTPException, Response
from dependency_injector.wiring import inject, Provide

from functools import wraps
from uuid import uuid4

from app.core.containers import Container
from app.db.session import scope


@inject
def commit_and_close_session(func):

    @wraps(func)
    @inject
    async def wrapper(db=Depends(Provide[Container.db]), *args, **kwargs,):
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
