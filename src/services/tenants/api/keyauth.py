# ovde pisemo API poziv za autentifikaciju preko Thilo BS Kljuca
import uuid



from typing import Dict
import base4.service.exceptions
from base4.api.crud import create_endpoints
from base4.utilities.security.jwt import DecodedToken, verify_token
from fastapi import Depends

import services.tenants.schemas as schemas
import services.tenants.services as services

from . import router


@router.post('/key-auth')
async def key_auth(request: schemas.KeyAuth) -> Dict:
    service = services.KeyAuthService()


    try:
        import services.tenants.models as models

        c = await models.Tenant.all().count()
    except Exception as e:
        raise

    try:
        return {'token': await service.generate_token(request.key) }
    except base4.service.exceptions.ServiceException as se:
        raise se.make_http_exception()
    except Exception as e:
        raise base4.service.exceptions.HTTPException(500,
                                                     detail={'code': 'INTERNAL_SERVER_ERROR', 'message': str(e)})

