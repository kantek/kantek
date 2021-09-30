import subprocess

from kantex.md import *

from utils import helpers
from utils.client import Client
from utils.pluginmgr import k, Command
from utils.tags import Tags


@k.command('update')
async def update(client: Client, event: Command, tags: Tags) -> None:
    """Run git pull and exit.

    This command assumes the bot is running under a process manager that automatically restarts it.

    Tags:
        update: Set to `silent` to silence any messages

    Examples:
        {cmd}
    """
    silent = tags.get('update', False)
    old_commit = helpers.get_commit()
    # region git pull
    if not silent:
        progess_message = await client.respond(event, KanTeXDocument(
            Section('Updating',
                    f'Running {Code("git pull")}')))
    else:
        await event.delete()

    proc = subprocess.call(['git', 'pull', '-q'])
    if proc != 0:
        msg = KanTeXDocument(
            Section('Error',
                    f'{Code("git")} returned non-zero exit code.',
                    'Please update manually'))
        if not silent:
            await progess_message.edit(str(msg))
        else:
            await client.respond(event, msg)
        return
    # endregion

    new_commit = helpers.get_commit()
    if old_commit == new_commit:
        await client.respond(
            event, KanTeXDocument(
                Section('No Update Available',
                        Italic('Doing nothing'))))
        return

    # region pip install
    proc = subprocess.call(['pip', 'install', '-Ur', 'requirements.txt'])
    if proc != 0:
        msg = KanTeXDocument(
            Section('Error',
                    f'{Code("pip")} returned non-zero exit code.',
                    'Please update manually'))
        if not silent:
            await progess_message.edit(str(msg))
        else:
            await client.respond(event, msg)
        return
    # endregion

    # region migrant
    if not silent:
        await progess_message.edit(str(KanTeXDocument(
            Section('Updating',
                    f'Running {Code("migrant apply --all")}'))))
    proc = subprocess.run(['migrant', 'apply', '--all'], stderr=subprocess.PIPE)
    if proc.returncode != 0:
        if b'MigrationComplete' not in proc.stderr:
            msg = KanTeXDocument(
                Section('Error',
                        f'{Code("migrant")} returned non-zero exit code.',
                        'Please update manually'))
            if not silent:
                await progess_message.edit(str(msg))
            else:
                await client.respond(event, msg)
            return
    # endregion

    if not silent:
        await progess_message.delete()
        await client.respond(
            event, KanTeXDocument(
                Section('Updated Kantek',
                        KeyValueItem('New commit', Link(new_commit, helpers.link_commit(new_commit))),
                        Italic('Restarting bot'))))
    await client.disconnect()
