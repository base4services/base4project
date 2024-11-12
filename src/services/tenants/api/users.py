from typing import Dict
import base4.service.exceptions
from base4.api.crud import create_endpoints
from base4.utilities.security.jwt import DecodedToken, verify_token
from fastapi import Depends

import services.tenants.schemas as schemas
import services.tenants.services as services

from . import router
from fastapi import Depends
from base4.utilities.security.jwt import DecodedToken, verify_token

from services.tenants.schemas.me import MeResponse, LoginResponse

@router.post('/users/login')
async def login(request: schemas.LoginRequest) -> LoginResponse:
    service = services.UsersService()
    try:
        return await service.login(request)
    except base4.service.exceptions.ServiceException as se:
        raise se.make_http_exception()
    except Exception as e:
        raise base4.service.exceptions.HTTPException(500,
                                                     detail={'code': 'INTERNAL_SERVER_ERROR', 'message': str(e)})


@router.get('/users/me')
async def login(session: DecodedToken = Depends(verify_token)) -> MeResponse:
    service = services.UsersService()
    try:
        return await service.me(session)
    except base4.service.exceptions.ServiceException as se:
        raise se.make_http_exception()
    except Exception as e:
        raise base4.service.exceptions.HTTPException(500,
                                                     detail={'code': 'INTERNAL_SERVER_ERROR', 'message': str(e)})


endpoints_config = {
    '/users': {
        'service': services.UsersService,
        'schema': schemas.UserSchema,
    },
}

create_endpoints(
    router, endpoints_config, service_name='tenants', singular_object_name='user', plural_object_name='users',
    functions={'get_single', 'create', 'update'}
)
