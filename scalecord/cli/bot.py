"""
* Commands: Bot Group
"""
# Third Party Imports
import click

# Local Imports
from scalecord._constants import initialize_environment
from scalecord._client import run_bot_client

"""
* Commands
"""


@click.command(
    name='run',
    help='Launch the Scalecord bot application.'
)
def launch_bot():
    """CLI command to launch the Scalecord bot application."""
    _bot = run_bot_client(
        env=initialize_environment())


"""
* Command Group
"""


@click.group(
    name='bot',
    commands={
        'run': launch_bot
    },
    invoke_without_command=True,
    context_settings={'ignore_unknown_options': True},
    help='Commands that provide direct bot control.'
)
@click.pass_context
def BotCLIGroup(ctx: click.Context):
    """Bot CLI group for top level bot control. If no subcommand is provided, launch the bot.

    Args:
        ctx: Click command context.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(launch_bot)
    pass


# Export command group
__all__ = ['BotCLIGroup']
