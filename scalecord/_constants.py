"""
* Constants
"""
# Standard Library Imports
import logging
import os
from logging import getLogger
from pathlib import Path
from typing import Optional

# Local Imports
from scalecord._state import _ROOT
from scalecord.utils.files import load_data_file, mkdir_full_perms

# Logger Object
logger = getLogger()
logger.setLevel(logging.INFO)

# Models
models = {}


class AppEnvironment:
    def __init__(self, **kwargs):
        self._path_root = kwargs.get(
            'path_root', _ROOT)
        if Path(os.getcwd()) != self._path_root:
            os.chdir(self._path_root)
        self._path_env = kwargs.get(
            'path_env', self.PATH_CONFIG / 'env.yml')
        self._loader_config = kwargs.get(
            'loader_config', None)
        try:
            self._env = load_data_file(
                self._path_env, self._loader_config)
        except (FileNotFoundError, OSError, ValueError):
            self._env = {}

    @property
    def CWD(self) -> Path:
        """Path: Current working directory of the project."""
        return self._path_root

    @property
    def PATH_ENV(self) -> Path:
        """Path: Path to the `env.yml` file."""
        return self._path_env

    @property
    def PATH_CACHE(self) -> Path:
        """Path: Path to the `.cache` directory."""
        return self._path_root / '.cache'

    @property
    def PATH_CONFIG(self) -> Path:
        """Path: Path to the `.config` directory."""
        return self._path_root / '.config'

    @property
    def PATH_MODELS(self) -> Path:
        """Path: Path to the `.models` directory."""
        return self._path_root / '.models'

    @property
    def GITHUB_ACCESS_TOKEN(self) -> Optional[str]:
        """str: GitHub personal access token used to raise GitHub API rate limits."""
        token = self._env.get('GITHUB_ACCESS_TOKEN', 'token_string_here').strip()
        if token in [None, '', 'token_string_here']:
            return
        return token

    @property
    def DISCORD_BOT_TOKEN(self) -> Optional[str]:
        """str: Discord bot token used to log the bot into Discord."""
        token = self._env.get('DISCORD_BOT_TOKEN', 'token_string_here').strip()
        if token in [None, '', 'token_string_here']:
            return
        return token

    @property
    def DISCORD_GUILD_IDS(self) -> set[int]:
        """list[str]: Discord server IDs to sync commands to instantly when the bot launches."""
        ids = self._env.get('DISCORD_GUILD_IDS', [])
        if not isinstance(ids, (list, tuple, set)):
            return set()
        return set(i for i in ids if isinstance(i, int))


def initialize() -> AppEnvironment:
    """Initializes the global state."""
    env_object = AppEnvironment()
    path_cache = env_object.CWD / '.cache'
    path_models = env_object.CWD / '.models'
    mkdir_full_perms(path_cache)
    mkdir_full_perms(path_models)
    return env_object


"""
* Global Environment Object
"""

ENV = initialize()
