"""
* Commands: Test Group
"""
# Standard Library Imports
from contextlib import suppress
from pathlib import Path
from pprint import pprint

# Third Party Imports
import click
import requests
import yarl
from omnitils.files import load_data_file

# Local Imports
from scalecord._constants import initialize_environment
from scalecord.utils import models


"""
* Commands
"""


@click.command(
    name='models',
    help='Validate all models.')
def test_models():
    """CLI command to validate all models."""
    ENV = initialize_environment()
    manifest_path = Path(ENV.PATH_CACHE / 'models.yml')
    models.verify_existing_models(
        manifest_path=manifest_path,
        models_path=ENV.PATH_MODELS)


@click.command(
    name='urls',
    help='Test model urls.'
)
def test_urls():
    """CLI command to launch the Scalecord bot application."""
    # Todo: Get rid of this janky thing
    ENV = initialize_environment()
    manifest_path = Path(ENV.PATH_CACHE / 'models.yml')
    data = load_data_file(manifest_path)
    good, bad, counts, always = {}, {}, {}, {}
    links = {k: list(v['resources'].values())[0] for k, v in data.items()}
    for i, (name, urls) in enumerate(links.items()):
        for u in urls:
            hostname = str(yarl.URL(u).host)
            counts.setdefault(hostname, 0)
            counts[hostname] += 1
            with suppress(Exception):
                with requests.get(u, stream=True) as r:
                    if r.status_code == 200:
                        content_length = r.headers.get('Content-Length', '')
                        if content_length and content_length.isnumeric():
                            good.setdefault(hostname, 0)
                            good[hostname] += 1
                            continue
            bad.setdefault(hostname, 0)
            bad[hostname] += 1
            continue
        print(f"#[{str(i).zfill(3)}] {name}")
    always = [n for n in good.keys() if n not in bad]
    print('=' * 120)
    print('--- TOTAL ---')
    print('=' * 120)
    pprint(counts, indent=2, compact=False, width=120)
    print('=' * 120)
    print('--- WORKED ---')
    print('=' * 120)
    pprint(good, indent=2, compact=False, width=120)
    print('=' * 120)
    print('--- DID NOT WORK ---')
    print('=' * 120)
    pprint(bad, indent=2, compact=False, width=120)
    print('=' * 120)
    print('--- ALWAYS WORKED ---')
    print('=' * 120)
    pprint(always, indent=2, compact=False, width=120)


"""
* Command Group
"""


@click.group(
    name='test',
    commands={
        'models': test_models,
        'urls': test_urls
    },
    invoke_without_command=True,
    context_settings={'ignore_unknown_options': True},
    help='Commands that facilitate unit testing and other application checks.',
)
@click.pass_context
def TestCLIGroup(ctx: click.Context):
    """Test CLI group for running checks and unit tests. If no subcommand is provided, test all models.

    Args:
        ctx: Click command context.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(test_models)
    pass


# Export command group
__all__ = ['TestCLIGroup']
