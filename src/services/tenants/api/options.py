from typing import Dict

from base4.api.crud import create_endpoints
from base4.utilities.security.jwt import DecodedToken, verify_token
from fastapi import Depends

import services.tenants.schemas as schemas
import services.tenants.services as services

from . import router

endpoints_config = {
    '/options': {
        'service': services.OptionService,
        'schema': schemas.OptionSchema,
    },
}

create_endpoints(
    router, endpoints_config, service_name='tenants', singular_object_name='option', plural_object_name='options', functions={'get_single', 'create', 'update'}
)


@router.get('/options/by-key/{key}', response_model=Dict[str, str])
async def get_option_by_key(key: str, _session: DecodedToken = Depends(verify_token)):
    service = services.OptionService()
    return await service.get_option_by_key(key)
