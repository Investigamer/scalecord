"""
* Constants
"""
# Standard Library Imports
import os
from functools import cached_property
import logging
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
    _env_defaults = {
        'DISCORD_BOT_TOKEN': '',
        'DISCORD_GUILD_IDS': set(),
        'GITHUB_ACCESS_TOKEN': '',
        'MAX_MODEL_SCALE': 4,
        'MIN_COLORS_IN': 3,
        'MIN_COLORS_OUT': 3,
        'OWNER_ONLY': 0
    }

    def __init__(self, **kwargs):

        # Establish current working directory
        self._path_root = kwargs.get(
            'path_root', Path(__file__).parent.parent)
        if Path(os.getcwd()) != self._path_root:
            os.chdir(self._path_root)

        # Create mandatory paths
        mkdir_full_perms(self.PATH_CONFIG)
        mkdir_full_perms(self.PATH_CACHE_IN)
        mkdir_full_perms(self.PATH_CACHE_OUT)
        mkdir_full_perms(self.PATH_MODELS)

        # Load environment variables
        try:
            self._env = load_data_file(
                path=self.PATH_CONFIG_ENV,
                config=kwargs.get('loader_config', None))
        except (FileNotFoundError, OSError, ValueError):
            self._env = {}

        # Set environment variables from os.environ when provided
        for n in self._env_defaults.keys():
            if self._env.get(n) not in [None, '']:
                continue
            self._env[n] = os.environ.get(n, self._env_defaults[n])

        # Join manifest data
        local_models = self.PATH_CONFIG / 'models.yml'
        local_manifest = get_manifest_data(local_models) if local_models.is_file() else {}
        all_models = get_manifest_data(self.PATH_CACHE_MODELS)
        all_models.update(local_manifest)

        # Load app models
        self._models = get_supported_models(
            models=all_models,
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
    def LOGR(self) -> logging.Logger:
        """Logger: Backend logging object."""
        logger = logging.getLogger('discord')
        logger.setLevel(logging.INFO)
        return logger

    """
    * Path Properties
    """

    @property
    def CWD(self) -> Path:
        """Path: Current working directory of the project."""
        return self._path_root

    @property
    def PATH_CONFIG(self) -> Path:
        """Path: Path to the `config` directory."""
        return self._path_root / 'config'

    @property
    def PATH_CONFIG_ENV(self) -> Path:
        """Path: Path to the `env.yml` file."""
        return self.PATH_CONFIG / 'env.yml'

    @property
    def PATH_CACHE(self) -> Path:
        """Path: Path to the `cache` directory."""
        return self._path_root / 'cache'

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
        """Path: Path to the `models` directory."""
        return self._path_root / 'models'

    """
    * Supported Environment Variables
    """

    @cached_property
    def DISCORD_BOT_TOKEN(self) -> str:
        """str: Discord bot token used to log the bot into Discord."""
        VAR_NAME = 'DISCORD_BOT_TOKEN'
        return str(self._env.get(VAR_NAME, self._env_defaults[VAR_NAME]).strip())

    @cached_property
    def DISCORD_GUILD_IDS(self) -> set[int]:
        """list[str]: Discord server IDs to sync commands to instantly when the bot launches."""
        VAR_NAME = 'DISCORD_GUILD_IDS'
        VAL = self._env.get(VAR_NAME, self._env_defaults[VAR_NAME])
        if isinstance(VAL, str) and ',' in VAL:
            VAL = [n.strip() for n in VAL.split(',')]
        if not VAL or not isinstance(VAL, (list, tuple, set)):
            return self._env_defaults[VAR_NAME]
        return set(
            int(i) for i in VAL
            if str(i).isnumeric()
        )

    @cached_property
    def GITHUB_ACCESS_TOKEN(self) -> str:
        """str: GitHub personal access token used to raise GitHub API rate limits."""
        VAR_NAME = 'GITHUB_ACCESS_TOKEN'
        return str(self._env.get(VAR_NAME, self._env_defaults[VAR_NAME]).strip())

    @cached_property
    def MAX_MODEL_SCALE(self) -> int:
        """int: Governs the max 'scale' value Scalecord will allow when indexing models."""
        VAR_NAME = 'MAX_MODEL_SCALE'
        VAL = self._env.get(VAR_NAME)
        if VAL and str(VAL).isdigit():
            return int(VAL)
        return self._env_defaults[VAR_NAME]

    @cached_property
    def MIN_COLORS_IN(self) -> int:
        """int: Governs the min inputChannels value Scalecord will allow when indexing models."""
        VAR_NAME = 'MIN_COLORS_IN'
        VAL = self._env.get(VAR_NAME)
        if VAL and str(VAL).isnumeric():
            return int(VAL)
        return self._env_defaults[VAR_NAME]

    @cached_property
    def MIN_COLORS_OUT(self) -> int:
        """int: Governs the min outputChannels value Scalecord will allow when indexing models."""
        VAR_NAME = 'MIN_COLORS_OUT'
        VAL = self._env.get(VAR_NAME)
        if VAL and str(VAL).isnumeric():
            return int(VAL)
        return self._env_defaults[VAR_NAME]

    @cached_property
    def OWNER_ONLY(self) -> bool:
        """bool: Governs whether upscaling commands can only be used by the server owner."""
        VAR_NAME = 'OWNER_ONLY'
        VAL = self._env.get(VAR_NAME, self._env_defaults[VAR_NAME])
        if str(VAL).lower() in ['1', 'on', 'yes', 'true']:
            return True
        return False

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
    return env_object
