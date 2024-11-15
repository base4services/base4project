import importlib
import json
import uuid
from typing import Any, AnyStr, Dict, Optional

import dotenv
import httpx
import pytest
from base4.utilities.files import get_project_root
from base4.utilities.service.startup import shutdown_event, startup_event
from fastapi import FastAPI
from httpx import Response

dotenv.load_dotenv(str(get_project_root() / '.env'))

@pytest.mark.asyncio
class TestBase:
    app: FastAPI = FastAPI()
    services = []

    current_logged_user = None

    async def create_item(self, endpoint, payload, expected_code=201, headers=None):
        res = await self.api('POST', f'/api/{endpoint}', _body=payload, _headers=headers)

        assert res.status_code == expected_code

        if expected_code in (200, 201):
            try:
                assert 'id' in res.json()
            except Exception as e:
                raise

        return res.json()

    async def update_item(self, endpoint, id: uuid.UUID, key, value, headers=None):
        res = await self.api('PATCH', f'/api/{endpoint}/{id}', _body={key: value}, _headers=headers)
        assert res.status_code == 200
        return res.json()

    async def validate_item(self, endpoint: str, id: uuid.UUID, expect_valid=True):
        res = await self.api('PATCH', f'/api/{endpoint}/{id}/validate')

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
        res = await self.api('DELETE', f'/api/{endpoint}/{_id}')
        return res

    async def fetch_item_by_id(self, endpoint, _id: uuid.UUID):
        res = await self.api('GET', f'/api/{endpoint}/{_id}')
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
            try:
                module = importlib.import_module(f'services.{service}.api')
                self.app.include_router(module.router, prefix=f"/api/{service}")
            except Exception as e:
                # try:
                #     module = importlib.import_module(f'base4services.services.{service}.api')
                #     self.app.include_router(module.router, prefix=f"/api/{service}")
                # except Exception as e2:
                raise

    async def setup(self):
        self.get_app()


    @pytest.fixture(autouse=True, scope="function")
    async def setup_fixture(self) -> None:
        """
        Fixture for tests of application.
        It will be executed everytime before each test and after.

        decorator:
                @pytest.fixture(autouse=True, scope="function")
                        autouse (bool): If true this fixture will be executed
                                                        brefore and after every test.
                        scope (str): This fixture is meant for function tests.

        :return: None
        """

        self.app.app_services = self.services
        await startup_event(self.services)
        await self.setup()
        yield
        await shutdown_event()

    async def api(self, _method: AnyStr, _endpoint: AnyStr, _body: Optional[Dict] = None, _params=None, _headers=None) -> Response | Dict:
        _method = _method.lower()

        params: Dict = {
            'url': _endpoint,
        }

        if not _headers:
            _headers = {}

        params['headers'] = _headers

        if 'Authorization' not in _headers:
            if self.current_logged_user and "token" in self.current_logged_user and self.current_logged_user["token"]:
                _headers['Authorization'] = f'Bearer {self.current_logged_user["token"]}'

        if _params:
            params['params'] = _params

        if _method not in ('delete', 'get'):

            if _body:
                _body = json.loads(json.dumps(_body, default=str))

            params['json'] = _body if _body else {}

        async with httpx.AsyncClient(app=self.app, base_url='https://test') as client:
            # Set the secure cookie
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
