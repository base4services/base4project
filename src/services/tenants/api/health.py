# THIS FILE IS GENERATED, DO NOT EDIT DIRECTLY
# USE GEN -s tenants --upgarde to install new version

from . import router


@router.get('/healthy')
async def healthy():
    # import services.tenants.models
    # try:
    #     c = await services.tenants.models.Tenant.all().count()
    # except Exception as e:
    #     raise
    return {'status': 'healthy', 'service': 'tenants', 'library': 'services'}
