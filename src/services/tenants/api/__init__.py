from fastapi import APIRouter

router = APIRouter()

from base4.utilities.service.startup import service as app

from .health import *
from .options import *
from .initialize import *
from .tenants import *
from .users import *

from .keyauth import *

app.include_router(router, prefix="/api/tenants")
