import asyncio
import json
import websockets
from websockets.http import Headers
from threedi_api_client.threedi_api_client import ThreediApiClient
from urllib.parse import urlparse
import asyncclick as click
import pprint
import signal
from pydantic import BaseSettings, Field

pp = pprint.PrettyPrinter(width=45, depth=1)


class Settings(BaseSettings):
    api_host: str = Field(..., env='API_HOST')
    proto: str = "wss"


class WebsocketClient(object):
    def __init__(self, jwt_token: str,
                 host, api_version, bearer='Bearer'):
        self.host = host
        self.proto = 'wss'
        self.api_version = api_version
        self.websocket = None
        self.do_listen = True
        self.bearer = bearer
        self.jwt_token = jwt_token

    async def listen(self):
        uri = f'{self.proto}://{self.host}/{self.api_version}/' +\
              f'active-simulations/'
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


async def shutdown(signal_inst: signal):
    """
    try to shut down gracefully
    """
    click.secho(f"Received exit signal {signal_inst.name}...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    click.secho("Canceling outstanding tasks")
    await asyncio.gather(*tasks)


@click.command()
@click.option(
    "--environment",
    required=True,
    type=click.Choice(["prod", "stag", "local"], case_sensitive=False),
    help="The destination environment",
)
async def main(environment):
    env_file = f"{environment}.env"
    settings = Settings(_env_file=env_file)
    parsed_url = urlparse(settings.api_host)
    host_name = parsed_url.netloc
    api_version = parsed_url.path.lstrip('/')
    client = ThreediApiClient(env_file)
    websocket_client = WebsocketClient(
        client.configuration.access_token,
        host=host_name, api_version=api_version
    )
    await asyncio.gather(
        websocket_client.listen(),
    )



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s, lambda s=s: asyncio.create_task(shutdown(s))
        )
    main(_anyio_backend="asyncio")  # or trio, or curio
