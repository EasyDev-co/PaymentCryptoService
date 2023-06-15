from pydantic import BaseModel


class User(BaseModel):
    id: str
    user_id: str


