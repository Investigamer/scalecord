"""
* Scalecord CLI Application
"""
# Third Party Imports
import click

# Local Imports
from scalecord.cli.bot import BotCLIGroup
from scalecord.cli.test import TestCLIGroup
from scalecord.cli.update import UpdateCLIGroup
from scalecord.cli.upscale import UpscaleCLIGroup
from scalecord.cli.generate import GenerateCLIGroup

"""
* CLI Application
"""


@click.group(
    commands={
        'bot': BotCLIGroup,
        'generate': GenerateCLIGroup,
        'test': TestCLIGroup,
        'update': UpdateCLIGroup,
        'upscale': UpscaleCLIGroup
    },
    invoke_without_command=True,
    context_settings={'ignore_unknown_options': True}
)
@click.pass_context
def CLI(ctx: click.Context):
    """CLI application entry point.

    Args:
        ctx: Click command context.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(BotCLIGroup)
    pass


# Export CLI
ScalecordCLI = CLI()
__all__ = ['ScalecordCLI']
