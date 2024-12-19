import importlib
import inspect
import uuid
from typing import Any, AnyStr, Dict, Optional
import os
import dotenv
import httpx
import pytest
import ujson as json
from base4.utilities.files import get_project_root
from base4.utilities.service.startup import shutdown_event, startup_event
from fastapi import FastAPI
from httpx import Response

project_root = get_project_root()

dotenv.load_dotenv(str(get_project_root() / '.env'))

@pytest.mark.asyncio
class TestBase:
    app: FastAPI = FastAPI()
    services = []

    current_logged_user = None

    async def create_item(self, endpoint, payload, expected_code=201, headers=None):
        res = await self.request(method='POST', url= f'/api/{endpoint}', json_data=payload, headers=headers)

        assert res.status_code == expected_code

        if expected_code in (200, 201):
            try:
                assert 'id' in res.json()
            except Exception as e:
                raise

        return res.json()

    async def update_item(self, endpoint, id: uuid.UUID, key, value, headers=None):
        res = await self.request('PATCH', f'/api/{endpoint}/{id}', json_data={key: value}, headers=headers)
        assert res.status_code == 200
        return res.json()

    async def validate_item(self, endpoint: str, id: uuid.UUID, expect_valid=True):
        res = await self.request('PATCH', f'/api/{endpoint}/{id}/validate')

        if expect_valid:
            assert res.status_code == 200
        else:
            assert res.status_code != 200

        return res.json()

    def assert_validation(self, validate, key):
        assert 'detail' in validate
        assert 'code' in validate['detail']
        assert validate['detail']['code'] == 'VALIDATION_ERROR'
        assert 'errors' in validate['detail'] and len(validate['detail']['errors']) > 0
        assert [key] == [x['field'] for x in validate['detail']['errors'] if x['field'] == key]

    async def delete_item(self, endpoint, _id: uuid.UUID):
        res = await self.request('DELETE', f'/api/{endpoint}/{_id}')
        return res

    async def fetch_item_by_id(self, endpoint, _id: uuid.UUID):
        res = await self.request('GET', f'/api/{endpoint}/{_id}')
        return res

    async def get_item_by_id(self, endpoint, _id: uuid.UUID):
        res = await self.fetch_item_by_id(endpoint, _id)

        assert res.status_code == 200
        return res.json()

    async def create_and_fetch_single_attribute_test(self, endpoint, schema, attribute: str, value: Any, compare_method=None, additional_attributes=None):
        try:
            payload = schema(**{attribute: value})
        except Exception as e:
            raise

        if additional_attributes:
            for key, value in additional_attributes.items():
                setattr(payload, key, value)

        create_res = await self.create_item(endpoint, payload.model_dump())

        assert 'id' in create_res
        _id = create_res['id']

        self._last_created_id = _id

        try:
            item = await self.get_item_by_id(endpoint, _id)
        except Exception as e:
            raise

        item_model = schema(**item)

        if not compare_method:

            if type(value) == list:
                ivalue = getattr(item_model, attribute)
                assert type(ivalue) == list
                assert len(value) == len(ivalue)
                for item in range(len(value)):
                    try:
                        eq = value[item].is_equal(ivalue[item])
                        assert eq
                    except Exception as e:
                        raise
            else:
                assert getattr(item_model, attribute) is not None and getattr(item_model, attribute) == value

            if hasattr(item_model, 'unique_id'):
                assert item_model.unique_id is not None

            return

        assert compare_method(item_model, attribute, value)

    def get_app(self):
        for service in self.services:
            if os.path.isdir(f"{project_root}/src/services/{service}"):
                if '__' not in service:
                    for api_handler_file in os.listdir(f"{project_root}/src/services/{service}/api"):
                        if '__' not in api_handler_file:
                            module = importlib.import_module(f'services.{service}.api.{api_handler_file[:-3]}')
                            for api_handler in inspect.getmembers(module):
                                try:
                                    if hasattr(api_handler[1], 'router'):
                                        obj = api_handler[1]
                                        self.app.include_router(obj.router, prefix=f"/api/{service}")
                                except Exception as e:
                                    continue
    async def setup(self):
        self.get_app()

    @pytest.fixture(autouse=True, scope="function")
    async def setup_fixture(self) -> None:
        self.app.app_services = self.services
        await startup_event(self.services)
        await self.setup()
        yield
        await shutdown_event()

    async def request(self, method: str, url: str, json_data: dict = None, data: dict = None, params=None, headers={}, files=[]):

        _method = method.lower()

        params: Dict = {
            'url': url,
        }

        if not headers:
            headers = {}

        params['headers'] = headers

        if 'Authorization' not in headers:
            if self.current_logged_user and "token" in self.current_logged_user and self.current_logged_user["token"]:
                headers['Authorization'] = f'Bearer {self.current_logged_user["token"]}'

        if params:
            params['params'] = params

        if _method not in ('delete', 'get'):

            if json_data:
                json_data = json.loads(json.dumps(json_data, default=str))

            params['json'] = json_data if json_data else {}

        async with httpx.AsyncClient(app=self.app, base_url='https://test') as client:
            client.cookies.set(
                'token',
                f'{self.current_logged_user["token"]}' if self.current_logged_user and "token" in self.current_logged_user else None,
            )
            func = getattr(client, _method, None)

            if not func:
                raise Exception(f'Invalid method: {_method}')

            try:
                response = await func(**params)
            except Exception as e:
                raise

        return response
