import asyncio
from urllib.parse import urlparse
import pprint
import signal

import asyncclick as click
from threedi_api_client.threedi_api_client import ThreediApiClient

from threedi_ws_client.ws_client import WebsocketClient
from threedi_ws_client.settings import get_settings

pp = pprint.PrettyPrinter(width=45, depth=1)


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
    "--env",
    required=True,
    type=click.Choice(["prod", "stag", "local"], case_sensitive=False),
    help="The destination environment",
)
async def main(env):
    env_file = f"{env}.env"
    proto = "ws" if env == "local" else "wss"
    settings = get_settings(env_file)
    parsed_url = urlparse(settings.api_host)
    host_name = parsed_url.netloc
    api_version = parsed_url.path.lstrip('/')
    client = ThreediApiClient(env_file)
    websocket_client = WebsocketClient(
        client.configuration.access_token,
        host_name=host_name,
        api_version=api_version,
        proto=proto
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
