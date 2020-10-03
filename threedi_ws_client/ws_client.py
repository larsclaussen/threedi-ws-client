import json
import websockets
from websockets.http import Headers
import asyncclick as click
import pprint

pp = pprint.PrettyPrinter(width=45, depth=1)


class WebsocketClient:
    def __init__(
        self,
        jwt_token: str,
        host_name: str,
        api_version: str,
        proto=str,
        bearer='Bearer'
    ):
        self.host = host_name
        self.proto = proto
        self.api_version = api_version
        self.websocket = None
        self.do_listen = True
        self.bearer = bearer
        self.jwt_token = jwt_token

    async def listen(self, endpoint: str):
        uri = f'{self.proto}://{self.host}/{self.api_version}/{endpoint}/'
        click.secho(f"Connecting to {uri}", fg="red", bold=True)
        headers = Headers(authorization=f'{self.bearer} {self.jwt_token}')
        async with websockets.connect(uri, extra_headers=headers) as websocket:
            self.websocket = websocket
            while self.do_listen:
                try:
                    data = await websocket.recv()
                    data = json.loads(data)
                    content = data["data"]
                    click.secho(pp.pprint(content), fg="blue", bold=True)
                except websockets.exceptions.ConnectionClosedOK:
                    self.do_listen = False

    async def close(self):
        self.do_listen = False
        await self.websocket.close()
