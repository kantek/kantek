import subprocess

from utils._config import Config
from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, Command


@k.command('update')
async def update(client: Client, event: Command) -> None:
    """Run git pull and exit.

    This command assumes the bot is running under a process manager that automatically restarts it.

    Examples:
        {cmd}
    """
    config = Config()
    progess_message = await client.respond(event, MDTeXDocument(
        Section('Updating',
                f'Running {Code("git pull")}')))
    subprocess.call(['git', 'pull', '-q'])
    proc = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
    new_commit = proc.decode().strip()
    await progess_message.delete()
    await client.respond(
        event,
        MDTeXDocument(
            Section('Updated Kantek',
                    KeyValueItem('New commit', Link(new_commit, f'{config.source_url}/commit/{new_commit}')),
                    Italic('Restarting bot'))))
    await client.disconnect()
    await client.aioclient.close()
