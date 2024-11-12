import datetime
from typing import Any, List

import pydantic


class CRApiHeader(pydantic.BaseModel):
    timestamp: datetime.datetime
    # date: datetime.date
    shop_id: str


class CRApi(pydantic.BaseModel):
    header: CRApiHeader
    data: List[Any]
