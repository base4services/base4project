from base4.utilities.logging.setup import class_exception_traceback_logging, get_logger
from base4.service.base import BaseService

import services.tenants.models as models
import services.tenants.schemas as schemas

from ._db_conn import get_conn_name

from base4.service.exceptions import ServiceException
import uuid

logger = get_logger()


@class_exception_traceback_logging(logger)
class TenantsService(BaseService[models.Tenant]):
    def __init__(self):
        super().__init__(schemas.TenantSchema, models.Tenant, get_conn_name())

    async def initialize(self, request: schemas.InitializeFirstTenantRequest):

        try:
            total_tenants = await self.model.all().count()
        except Exception as e:
            raise

        if total_tenants > 0:
            raise ServiceException('CAN_NOT_INITIALIZE_TENANT', 'Primary tenant already initialized')

        try:
            tenant = self.model(
                logged_user_id=None,
                code=request.code,
                display_name=request.display_name if request.display_name else request.code.capitalize())

            await tenant.save()

            import services.tenants.services.users as users_service
            us = users_service.UsersService()

            if not request.master_user_password:
                request.master_user_password = str(uuid.uuid4())

            user = await us.create_master_user_only_if_there_is_one_tenant_and_no_users(tenant,
                                                                                 request.master_username,
                                                                                 request.master_user_password)


        except Exception as e:
            raise

        return {'id': str(tenant.id), 'id_user': user.id}
