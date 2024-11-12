
from typing import Dict

from base4.api.crud import create_endpoints
from base4.utilities.security.jwt import DecodedToken, verify_token
from fastapi import Depends

import services.tenants.schemas as schemas
import services.tenants.services as services

from . import router

endpoints_config = {
    '': {
        'service': services.TenantsService,
        'schema': schemas.TenantSchema,
    },
}

create_endpoints(
    router, endpoints_config, service_name='tenants', singular_object_name='tenant', plural_object_name='tenantss', functions={'get_single', 'create', 'update', 'get'}
)
