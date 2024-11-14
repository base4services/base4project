import pydash
import uvicorn
from base4 import configuration
from base4.utilities.service.startup import get_service, run_server
from fastapi import FastAPI

service: FastAPI = get_service()

if __name__ == '__main__':
    cfg = configuration('services')

    monolith = pydash.get(cfg, 'general.monolith')
    if not monolith:
        raise Exception('missing monolith config')

    if pydash.get(cfg, 'general.app_type') in ('docker-monolith', 'monolith'):

        config = uvicorn.Config("__main__:service", **monolith)
        run_server(config)
    else:
        import sys

        if len(sys.argv) != 2:
            print("missing service name")
            sys.exit(15)

        config = uvicorn.Config("__main__:service", **monolith)
        run_server(config, single_service=sys.argv[1])
