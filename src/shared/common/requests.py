from fastapi import Request
from base4.service.exceptions import ServiceException


async def get_tenant_from_headers(tenants_model_class, request: Request):
    if not request.headers.get('x-tenant-id'):
        raise ServiceException('X-TENANT-ID_MISSING_IN_HEADERS', 'X-Tenant-ID missing in headers', status_code=406)

    try:
        return await tenants_model_class.filter(id=request.headers.get('x-tenant-id'),
                                                is_valid=True,
                                                is_deleted=False).get_or_none()
    except Exception as e:
        raise ServiceException('TENANT_NOT_FOUND', 'Tenant not found')
