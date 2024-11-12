import uuid
from typing import Optional
import pydantic
import datetime

class MeResponse(pydantic.BaseModel):
    id: uuid.UUID
    username: str
    id_tenant: uuid.UUID

    '''
    password expiring at
    password last changed
    last login
    '''

class LoginResponse(pydantic.BaseModel):
    token: str
    exp: datetime.datetime
    me: MeResponse