from typing import Optional

import pydantic


class LoginRequest(pydantic.BaseModel):
    username: str
    password: str