import pydash
import uvicorn
from base4 import configuration
from base4.utilities.service.startup import get_service, run_server
from fastapi import FastAPI
import sys

service: FastAPI = get_service()

if __name__ == '__main__':
    cfg = configuration('services')

    monolith = pydash.get(cfg, 'general.monolith')
    if not monolith:
        raise Exception('missing monolith config')
    
    config = uvicorn.Config("__main__:service", **monolith)
    
    if pydash.get(cfg, 'general.app_type') in ('docker-monolith', 'monolith'):
        run_server(config, service)
    else:

        if len(sys.argv) != 2:
            print("missing service name")
            sys.exit(15)
        run_server(config, service, single_service=sys.argv[1])
