from pydantic import BaseModel


class Webhook(BaseModel):
    """
    {
        "update_id": 761092606,
        "message": {
            "message_id": 1,
            "from": {
                "id": 411683152,
                "is_bot": False,
                "first_name": "Sukriti",
                "last_name": "Bajpai",
                "username": "Sonalibajpai62",
                "language_code": "en"
            },
            "chat": {
                "id": 411683152,
                "first_name": "Sukriti",
                "last_name": "Bajpai",
                "username": "Sonalibajpai62",
                "type": "private"
            },
            "date": 1630764051,
            "text": "/start WhatIsIt",
            "entities": [
                {
                    "offset": 0,
                    "length": 6,
                    "type": "bot_command"
                }
            ]
        }
    }
    """
    update_id: int
    message: dict = None
    callback_query: dict = None
    