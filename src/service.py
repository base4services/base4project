import importlib
import os
import signal

import pydash
import uvicorn
import yaml
from base4 import configuration
from base4.utilities.service.startup import get_service
from fastapi import FastAPI

service: FastAPI = get_service()

current_file_path = os.path.abspath(os.path.dirname(__file__))

class GracefulShutdown:
    def __init__(self):
        self.should_exit = False
        self.exit_code = 0
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)

    def handle_signal(self, signum, frame):
        print(f"Received signal {signum}. Initiating shutdown...")
        self.should_exit = True
        self.exit_code = signum  # Standard exit code for signals


def load_services(single_service=None):
    with open(os.path.join(current_file_path + '/config/services.yaml')) as f:
        services = yaml.safe_load(f)
        for service in services['services']:
            svc_name = list(service.keys())[0]

            if single_service and svc_name != single_service:
                continue

            try:
                importlib.import_module(f"services.{svc_name}.api")
            except Exception as e:
                raise
                # ...
                # importlib.import_module(f"base4services.services.{svc_name}.api")
                # ...

def run_server(config, single_service=None):
    server = uvicorn.Server(config)
    shutdown_handler = GracefulShutdown()

    async def custom_on_tick():
        if shutdown_handler.should_exit:
            await server.shutdown()

    server.force_exit = False
    server.custom_on_tick = custom_on_tick

    load_services(single_service=single_service)

    try:
        server.run()
    except Exception as e:
        print(f"Server stopped unexpectedly: {e}")
    finally:
        print(f"Server has been shut down. Exit code: {shutdown_handler.exit_code}")
        sys.exit(shutdown_handler.exit_code)


if __name__ == '__main__':
    cfg = configuration('services')

    monolith = pydash.get(cfg, 'general.monolith')
    if not monolith:
        raise Exception('missing monolith config')

    if pydash.get(cfg, 'general.app_type') in ('docker-monolith','monolith'):

        config = uvicorn.Config("__main__:service", **monolith)
        run_server(config)
    else:
        import sys
        if len(sys.argv) != 2:
            print("missing service name")
            sys.exit(15)

        config = uvicorn.Config("__main__:service", **monolith)
        run_server(config, single_service=sys.argv[1])
