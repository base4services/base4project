from pydoc import resolve
from typing import Dict

import base4.service.exceptions
from base4.api.crud import create_endpoints
from base4.utilities.security.jwt import DecodedToken, verify_token
from fastapi import Depends

import services.tenants.schemas as schemas
import services.tenants.services as services

from . import router


@router.post('/initialize')
async def initialize_tenant(request: schemas.InitializeFirstTenantRequest) -> Dict:
    service = services.TenantsService()
    try:
        res = await service.initialize(request)
        return res

    except base4.service.exceptions.ServiceException as se:
        raise se.make_http_exception()
    except Exception as e:
        raise base4.service.exceptions.HTTPException(500, detail={'code': 'INTERNAL_SERVER_ERROR', 'message': str(e)})
