from typing import Optional

import pydantic


class KeyAuth(pydantic.BaseModel):
    key: str