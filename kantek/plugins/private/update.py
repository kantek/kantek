from asyncio import subprocess

from utils._config import Config
from utils.client import KantekClient
from utils.mdtex import *
from utils.pluginmgr import k, Command


@k.command('update')
async def update(client: KantekClient, event: Command) -> None:
    """Run git pull and exit.

    This command assumes the bot is running under a process manager that automatically restarts it.

    Examples:
        {cmd}
    """
    config = Config()
    progess_message = await client.respond(event, MDTeXDocument(
        Section('Updating',
                f'Running {Code("git pull")}')))
    await subprocess.create_subprocess_shell('git pull -q')
    proc = await subprocess.create_subprocess_shell('git rev-parse --short HEAD',
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE)
    new_commit = (await proc.stdout.read()).decode().strip()
    await progess_message.delete()
    await client.respond(
        event,
        MDTeXDocument(
            Section('Updated kantek',
                    KeyValueItem('New commit', Link(new_commit, f'{config.source_url}/commit/{new_commit}')),
                    Italic('Restarting bot'))))
    await client.disconnect()
