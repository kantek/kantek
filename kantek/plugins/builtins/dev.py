from utils.client import Client
from utils.mdtex import *
from utils.pluginmgr import k, _Command, _Signature


@k.command('dev', document=False)
async def dev() -> None:
    """Random convenience functions for the bot developers.

    These are unsupported. Don't try to get support for them.
    """
    pass


@dev.subcommand()
async def requires(client: Client, args, kwargs) -> MDTeXDocument:
    """List all commands that require a certain argument to their callbacks.

    Arguments:
        `attribute`: The attribute that should be checked for
        `hide`: Hide command if the attribute is the value. Pass None to show everything. Defaults to False.

    Examples:
        {cmd} db
        {cmd} msg hide: None
        {cmd} client hide: True
    """
    plugins = client.plugin_mgr
    _requires = args[0]
    hide = kwargs.get('hide', False)
    supported_args = _Signature.__annotations__.keys()
    if _requires not in supported_args:
        return MDTeXDocument(
            Section('Error',
                    KeyValueItem('Unsupported argument', Code(_requires)),
                    KeyValueItem('Supported', ', '.join(map(str, map(Code, supported_args))))))
    result = Section('Result')
    cmd: _Command
    for name, cmd in plugins.commands.items():
        req = cmd.signature.__dict__[_requires]
        _cmd = SubSection(name)
        if req is not hide:
            _cmd.append(KeyValueItem(_requires, req))
        if cmd.subcommands:
            for scname, scmd in cmd.subcommands.items():
                screq = scmd.args.__dict__[_requires]
                if screq is not hide:
                    _scmd = SubSubSection(scname,
                                          KeyValueItem(_requires, screq))
                    _cmd.append(_scmd)
        if _cmd.items:
            result.append(_cmd)
    return MDTeXDocument(result)
