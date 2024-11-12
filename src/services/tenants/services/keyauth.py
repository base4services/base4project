from pydantic.v1.datetime_parse import datetime_re
import dotenv

from base4.utilities.logging.setup import class_exception_traceback_logging, get_logger
from base4.service.base import BaseService

import services.tenants.models as models
import services.tenants.schemas as schemas

from ._db_conn import get_conn_name

from base4.service.exceptions import ServiceException
import os
import datetime
import jwt
import json
import httpx
import slugify

logger = get_logger()

from base4.utilities.files import read_file
dotenv.load_dotenv()
default_id_user = os.getenv('DEFAULT_ID_USER', '00000000-0000-0000-0000-000000000000')

private_key = read_file('security/private_key.pem')
public_key = read_file('security/public_key.pem')


async def check_biznisoft_licence_on_thilo(key):

    try:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(f'https://biznisoft.thilo.services/api/software_licence/get-bp-by-key',
                                         data=json.dumps({'key': key}))
            except Exception as e:
                raise

            if response.status_code != 200:
                raise ServiceException(401, {'code': 'UNAUTHORIZED', 'message': 'Invalid key'})

            return response.json()
    except Exception as e:
        raise

@class_exception_traceback_logging(logger)
class KeyAuthService(BaseService[models.Tenant]):
    def __init__(self):
        super().__init__(schemas.UserSchema, models.User, get_conn_name())

    async def check_by_key(self, key):
        return {'business_partner-slug': 'digital-cube', }

    async def generate_token(self, key: str):
        licence_info = await check_biznisoft_licence_on_thilo(key)

        slug = slugify.slugify(licence_info['bp']['display_name']+'-'+licence_info['bp']['tax_number'])
        slug = slug[:255]

        tenant_display_name = licence_info['bp']['display_name']+' ('+licence_info['bp']['tax_number']+')'




        try:
            q= models.Tenant.filter(code=slug)
            s=q.sql()
            c = await models.Tenant.all().count()

            tenant = await models.Tenant.filter(code=slug).get_or_none()
        except Exception as e:
            raise

        if not tenant:
            try:
                tenant = models.Tenant(code=slug,
                                       display_name=tenant_display_name,
                                       logged_user_id=default_id_user,
                                       )
                await tenant.save()
            except Exception as e:
                raise
        service_user = await models.User.filter(username='service',
                                                tenant=tenant
                                                ).get_or_none()
        if not service_user:
            try:
                service_user = models.User(username='service',
                                           tenant=tenant,
                                           password=key,
                                           logged_user_id=default_id_user,
                                           )
                await service_user.save()
            except Exception as e:
                raise
        try:
            payload = {
                'username': service_user.username,
                'id_user': str(service_user.id),
                'id_tenant': str(service_user.tenant_id),
                'exp': int(datetime.datetime.fromisoformat(licence_info['licence']['expiration_date']).timestamp()),
                # 'exp': datetime.datetime.now() + datetime.timedelta(days=2),

            }
        except Exception as e:
            raise

        global private_key

        try:
            encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')
        except Exception as e:
            raise
        return encoded_jwt
