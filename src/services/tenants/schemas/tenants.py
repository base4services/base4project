from typing import Optional

import pydantic


class InitializeFirstTenantRequest(pydantic.BaseModel):
    code: str
    display_name: Optional[None | str] = None

    master_username: Optional[None | str] = 'master'
    master_user_password: Optional[None | str] = None