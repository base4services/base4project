import dotenv
import os
from base4.utilities.logging.setup import class_exception_traceback_logging, get_logger
from base4.service.base import BaseService

import services.tenants.models as models
import services.tenants.schemas as schemas

from ._db_conn import get_conn_name


from base4.service.exceptions import ServiceException
import os
import datetime
import jwt

from services.tenants.schemas.me import MeResponse, LoginResponse

logger = get_logger()

from base4.utilities.files import read_file

dotenv.load_dotenv()
default_id_user = os.getenv('DEFAULT_ID_USER', '00000000-0000-0000-0000-000000000000')


private_key = read_file('security/private_key.pem')
public_key = read_file('security/public_key.pem')


@class_exception_traceback_logging(logger)
class UsersService(BaseService[models.Tenant]):
    def __init__(self):
        super().__init__(schemas.UserSchema, models.User, get_conn_name())

    def check_password(self, user, password):

        # TODO - Implement bcrypt, and also mock bcrypt in tests, so in tests we will use plain text passwords

        return user.password == password

    def generate_token_payload(self, user):
        return {
            'username': user.username,
            'id_user': str(user.id),
            'id_tenant': str(user.tenant_id),
            'exp': int((datetime.datetime.now() + datetime.timedelta(days=2)).timestamp()),
        }

    def generate_token(self, payload):
        # JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'secret')

        global private_key

        try:

            encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256')
            # encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        except Exception as e:
            raise
        return encoded_jwt

    async def login(self, request: schemas.LoginRequest) -> LoginResponse:

        try:
            user = await self.model.get(username=request.username)
        except Exception as e:
            raise

        if not user and not self.check_password(user, request.password):
            raise ServiceException('INVALID_CREDENTIALS', 'Invalid credentials')

        payload = self.generate_token_payload(user)

        try:
            me = MeResponse(
                id=user.id,
                username=user.username,
                id_tenant=user.tenant_id,
            )

            res = LoginResponse(token=self.generate_token(payload),
                                 exp=payload['exp'],
                                 me=me)

            return res

        except Exception as e:
            raise

    async def me(self, session) -> MeResponse:

        try:
            me = await self.model.filter(id=session.user_id, tenant_id=session.tenant_id,
                                         is_deleted=False).get_or_none()

            res = MeResponse(
                id=me.id,
                username=me.username,
                id_tenant=me.tenant_id,
            )

        except Exception as e:
            raise

        return res

    async def create_master_user_only_if_there_is_one_tenant_and_no_users(self, tenant, username, password):

        nr_of_users = await self.model.all().count()
        if nr_of_users > 0:
            raise ServiceException('CAN_NOT_INITIALIZE_TENANT',
                                   'Primary tenant already initialized')

        try:
            user = self.model(
                logged_user_id=default_id_user,
                tenant=tenant,
                username=username,
                password=password,
            )
        except Exception as e:
            raise

        await user.save()
        return user
