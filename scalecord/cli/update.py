"""
* Commands: Update Group
"""
# Standard Library Imports
from pathlib import Path

# Third Party Imports
import click
from omnitils.files_data import load_data_file

# Local Imports
from scalecord._constants import initialize_environment
from scalecord.utils.models import update_model_data, download_model

"""
* Commands
"""


@click.command(
    name='data',
    help='Update all manifest data files.'
)
def update_data():
    """CLI command to launch the Scalecord bot application."""
    ENV = initialize_environment()
    update_model_data(
        cache_path=ENV.PATH_CACHE,
        manifest_map=ENV.MANIFEST_URLS,
        max_scale=ENV.MAX_MODEL_SCALE)


@click.command(
    name='models',
    help='Download and update all models.'
)
def update_models():
    """CLI command to launch the Scalecord bot application."""
    # Todo: Add support for indirect links.
    ENV = initialize_environment()
    manifest_path = Path(ENV.PATH_CACHE / 'models.yml')
    data = load_data_file(manifest_path)
    mods = {}
    for name, data in data.items():
        for url in [url for url in sum(data['resources'].values(), [])]:
            if url.endswith('.pth'):
                mods[name] = url
    for name, url in mods.items():
        path = Path(ENV.PATH_MODELS, name).with_suffix('.pth')
        if path.is_file():
            # Todo: Check if existing file needs an update
            continue
        download_model(url=url, path=path)


"""
* Command Group
"""


@click.group(
    name='update',
    commands={
        'data': update_data,
        'models': update_models
    },
    invoke_without_command=True,
    context_settings={'ignore_unknown_options': True},
    help='Commands that pull updates for data, models, etc.',
)
@click.pass_context
def UpdateCLIGroup(ctx: click.Context):
    """Update CLI group for running app updates. If no subcommand is provided, update the manifest data.

    Args:
        ctx: Click command context.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(update_data)
    pass


# Export command group
__all__ = ['UpdateCLIGroup']
