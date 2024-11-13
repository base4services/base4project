from base4.ws.service import BaseSocketServer


class BSOneSocketServer(BaseSocketServer):
	def __init__(self):
		super().__init__()
		print("BSOneSocketServer Initialized")


# https://admin.socket.io/#/servers
# 	# http://127.0.0.1:8000
# 	# admin
# 	# paswd
# 	# /admin
# 	# /socket.io

# uvicorn ws.service:app --host 0.0.0.0 --port 8000
app = BSOneSocketServer().sio_app
