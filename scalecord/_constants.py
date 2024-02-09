"""
* Constants
"""
# Standard Library Imports
import os
from functools import cached_property
from logging import Logger, getLogger
from pathlib import Path


# Third Party Imports
from omnitils.files_data import load_data_file
from omnitils.folders import mkdir_full_perms

# Local Imports
from scalecord.types.models import ModelManifestMap, ModelManifestMapDefaults, ScalecordModel, OMDBTag
from scalecord.utils.models import get_supported_models, get_manifest_data

"""
* Global Environment Class
"""


class AppEnvironment:
    def __init__(self, **kwargs):

        # Establish current working directory
        self._path_root = kwargs.get(
            'path_root', Path(__file__).parent.parent)
        if Path(os.getcwd()) != self._path_root:
            os.chdir(self._path_root)

        # Load environment variables
        try:
            self._env = load_data_file(
                path=self.PATH_CONFIG_ENV,
                config=kwargs.get('loader_config', None))
        except (FileNotFoundError, OSError, ValueError):
            self._env = {}

        # Load app models
        self._models = get_supported_models(
            models=get_manifest_data(self.PATH_CACHE_MODELS),
            tags=get_manifest_data(self.PATH_CACHE_TAGS),
            models_path=self.PATH_MODELS)

        # Load model tags
        self._tags = get_manifest_data(self.PATH_CACHE_TAGS)

        # Load model architectures
        self._arch = get_manifest_data(self.PATH_CACHE_ARCH)

    """
    * Global Objects
    """

    @cached_property
    def LOGR(self) -> Logger:
        return getLogger()

    """
    * Path Properties
    """

    @property
    def CWD(self) -> Path:
        """Path: Current working directory of the project."""
        return self._path_root

    @property
    def PATH_CONFIG(self) -> Path:
        """Path: Path to the `.config` directory."""
        return self._path_root / '.config'

    @property
    def PATH_CONFIG_ENV(self) -> Path:
        """Path: Path to the `env.yml` file."""
        return self.PATH_CONFIG / 'env.yml'

    @property
    def PATH_CACHE(self) -> Path:
        """Path: Path to the `.cache` directory."""
        return self._path_root / '.cache'

    @property
    def PATH_CACHE_MODELS(self) -> Path:
        """Path: Path to the `models.yml` manifest file."""
        return self.PATH_CACHE / 'models.yml'

    @property
    def PATH_CACHE_TAGS(self) -> Path:
        """Path: Path to the `tags.yml` manifest file."""
        return self.PATH_CACHE / 'tags.yml'

    @property
    def PATH_CACHE_IN(self) -> Path:
        """Path: Path to the image input directory."""
        return self.PATH_CACHE / 'in'

    @property
    def PATH_CACHE_OUT(self) -> Path:
        """Path: Path to the image output directory."""
        return self.PATH_CACHE / 'out'

    @property
    def PATH_CACHE_ARCH(self) -> Path:
        """Path: Path to the `architectures.yml` manifest file."""
        return self.PATH_CACHE / 'architectures.yml'

    @property
    def PATH_MODELS(self) -> Path:
        """Path: Path to the `.models` directory."""
        return self._path_root / '.models'

    """
    * API Tokens
    """

    @cached_property
    def GITHUB_ACCESS_TOKEN(self) -> str:
        """str: GitHub personal access token used to raise GitHub API rate limits."""
        token = self._env.get('GITHUB_ACCESS_TOKEN', 'token_string_here').strip()
        if token in [None, '', 'token_string_here']:
            return ''
        return token

    @cached_property
    def DISCORD_BOT_TOKEN(self) -> str:
        """str: Discord bot token used to log the bot into Discord."""
        token = self._env.get('DISCORD_BOT_TOKEN', 'token_string_here').strip()
        if token in [None, '', 'token_string_here']:
            return ''
        return token

    """
    * Discord Settings
    """

    @cached_property
    def DISCORD_GUILD_IDS(self) -> set[int]:
        """list[str]: Discord server IDs to sync commands to instantly when the bot launches."""
        ids = self._env.get('DISCORD_GUILD_IDS', [])
        if not isinstance(ids, (list, tuple, set)):
            return set()
        return set(i for i in ids if isinstance(i, int))

    """
    * Model Data
    """

    @property
    def MANIFEST_URLS(self) -> ModelManifestMap:
        """ModelManifestMap: Maps manifest resources to source URLs."""
        return ModelManifestMapDefaults

    @property
    def MODELS(self) -> dict[str, ScalecordModel]:
        """dict[str, ScalecordModel]: Map of all models."""
        return self._models

    @property
    def TAGS(self) -> dict[str, OMDBTag]:
        """dict[str, OMDBTag]: Map of all tags."""
        return self._tags

    @property
    def ARCHITECTURES(self) -> dict[str, str]:
        """dict[str, str]: Map of all architectures."""
        return self._arch


def initialize_environment(**kwargs) -> AppEnvironment:
    """Initializes the global state."""
    env_object = AppEnvironment(**kwargs)
    path_cache = env_object.CWD / '.cache'
    path_models = env_object.CWD / '.models'
    mkdir_full_perms(path_cache)
    mkdir_full_perms(path_models)
    return env_object
