from typing import Dict

from base4.service.base import BaseService
from base4.utilities.logging.setup import class_exception_traceback_logging, get_logger
from fastapi.exceptions import HTTPException

import services.__SERVICE_NAME__.models as models
import services.__SERVICE_NAME__.schemas as schemas

from ._db_conn import get_conn_name

logger = get_logger()


@class_exception_traceback_logging(logger)
class OptionService(BaseService[models.Option]):
    def __init__(self):
        super().__init__(schemas.OptionSchema, models.Option, get_conn_name())

    async def get_option_by_key(self, key: str) -> Dict[str, str]:
        res = await models.Option.filter(key=key).get_or_none()

        if not res:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "parameter": "option", "message": f"option for key {key} not found"})

        return {'id': str(res.id), 'value': res.value}
