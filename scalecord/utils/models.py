"""
* Utils: Models
"""
# Standard Library Imports
import os
from contextlib import suppress
from logging import getLogger
from pathlib import Path
from typing import Optional

# Third Party Imports
import requests
import yarl
from omnitils.fetch import download_file
from omnitils.files import get_sha256, dump_data_file, load_data_file, mkdir_full_perms
from tqdm import tqdm

# Local Imports
from scalecord.types.models import (
    ModelResource,
    OMDBModel,
    ManifestModel, ModelManifestMap, OMDBArchitecture, ScalecordModel, OMDBTag
)


"""
* Building Manifest Data
"""


def get_model_resources(resources: list[ModelResource]) -> dict[str, list[str]]:
    """Checks a list of model resources to remove any with unsupported types or platforms and prioritize
    resources with a direct download link. If none are direct links, return all supported resources.

    Args:
        resources: Resources list from OpenModelDB manifest.

    Returns:
        Dictionary mapping sha256 strings to their URL source.
    """
    formatted: dict[str, list[str]] = {}
    for r in resources:

        # Skip non-PyTorch models
        if r['type'] != 'pth' or r['platform'] != 'pytorch':
            continue

        # Check for a pre-existing matching sha256
        if r['sha256'] in formatted:
            if any([n.endswith('.pth') for n in formatted[r['sha256']]]):
                # Ship this resource if direct link already accounted for
                continue
        formatted.setdefault(r['sha256'], [])

        # Check for a direct download link
        for u in r['urls']:
            if u.endswith('.pth'):
                # Only use direct link
                formatted[r['sha256']] = [u]
                break
            formatted[r['sha256']].append(u)

    # Return formatted resources
    return formatted


def format_architecture_data(data: dict[str, OMDBArchitecture]) -> dict[str, str]:
    """Format architecture data from OpenModelDB to remove unsupported architectures."""
    return {
        k: v['name'] for k, v in data.items()
        if v['input'] == 'image' and 'pytorch' in v['compatiblePlatforms']
    }


def format_model_data(
        data: dict[str, OMDBModel],
        architectures: dict[str, str],
        max_scale: int = 4
) -> dict[str, ManifestModel]:
    """Formats model data retrieved from OpenModelDB to reduce filesize.

    Args:
        data: Model manifest data.
        architectures: Supported architectures, exclude any models not found in this data.
        max_scale: Exclude all models above this scale factor, defaults to 8.

    Returns:
        Formatted manifest data.
    """
    result = {}
    for k, v in data.items():
        # Ensure resources contains a PyTorch supported model
        resources = get_model_resources(v['resources'])
        if not resources:
            continue
        # Exclude non-RGB/RGBA models
        if v['inputChannels'] < 3:
            continue
        if v['outputChannels'] < 3:
            continue
        # Exclude unsupported architectures
        if v['architecture'] not in architectures:
            continue
        # Exclude models above max_scale
        if v['scale'] > max_scale:
            continue
        result[k] = ManifestModel(
            architecture=v['architecture'],
            name=v['name'],
            resources=resources,
            scale=v['scale'],
            tags=v['tags']
        )
    return result


def download_manifest_data(url: str) -> dict:
    """Downloads manifest data from a given URL.

    Args:
        url: URL where a manifest file is hosted.

    Returns:
        Loaded data of the retrieved manifest file. If request issue occurred, return an empty dict.
    """
    with requests.get(url) as r:
        if r.status_code != 200:
            getLogger().warning(f"Unable to retrieve '{yarl.URL(url).name}' manifest.")
            return {}
        with suppress(Exception):
            data = r.json()
            return data
    return {}


def update_model_data(
    cache_path: Path,
    manifest_map: ModelManifestMap,
    max_scale: int = 4
) -> Optional[dict[str, ManifestModel]]:
    """Downloads the latest manifest files from OpenModelDB and updates the models manifest.

    Args:
        cache_path: Path to the cache directory.
        manifest_map: Dictionary mapping manifest resources to a source URL.
        max_scale: Exclude all models above this scale factor, defaults to 8.

    Returns:
        Updated and formatted model manifest data.
    """

    # Retrieve supported tag categories
    category_data = download_manifest_data(manifest_map['tag_categories'])
    tags_allowed = list(set(category_data['subject']['tags'] + category_data['purpose']['tags']))

    # Retrieve and dump supported tags
    tags_data = download_manifest_data(manifest_map['tags'])
    tags: dict[str, OMDBTag] = {k: v for k, v in tags_data.items() if k in tags_allowed}
    dump_data_file(
        obj=tags,
        path=Path(cache_path, 'tags.yml'))

    # Retrieve, format, and dump format architectures data
    arch_data = download_manifest_data(manifest_map['architectures'])
    formatted_arch_data = format_architecture_data(arch_data)
    dump_data_file(
        obj=formatted_arch_data,
        path=Path(cache_path, 'architectures.yml'))

    # Retrieve, format, and dump model data
    model_data = download_manifest_data(manifest_map['models'])
    formatted_model_data = format_model_data(
        data=model_data,
        architectures=formatted_arch_data,
        max_scale=max_scale)
    dump_data_file(
        obj=formatted_model_data,
        path=Path(cache_path, 'models.yml'))
    return formatted_model_data


"""
* Retrieving Manifest Data
"""


def get_manifest_data(path: Path) -> dict:
    """Retrieves a loaded data object from a provided manifest file.

    Args:
        path: Path to the manifest file.

    Returns:
        Dictionary containing the loaded data from the manifest file.
    """
    with suppress(Exception):
        data = load_data_file(path)
        return data
    getLogger().error(f"Manifest file not found: {path.name}\n"
                      "Generating empty one.")
    dump_data_file({}, path)
    return {}


"""
* Building Model Repository
"""


def verify_existing_models(manifest_path: Path, models_path: Path) -> None:
    """Audits the current models manifest file. Removes manifest files for any
    unsupported models and generates a blacklist. Generates a whitelist for
    supported models.

    Todo:
        Finish this.

    Args:
        manifest_path: Path to the model data manifest path (usually a `models.yml` file).
        models_path: Path where PTH model files are placed.

    Returns:
        Dictionary of models that were unverified or not supported.
    """
    rename_existing_models(manifest_path, models_path)


def rename_existing_models(manifest_path: Path, models_path: Path) -> None:
    """Rename existing models to match data found in the manifest file.

    Args:
        manifest_path: Path to the model data manifest path (usually a `models.yml` file).
        models_path: Path where PTH model files are placed.
    """

    # Set unrecognized path and load model data
    hashes, move_to = {}, models_path / 'unrecognized'
    try:
        models = load_data_file(manifest_path)
    except (FileNotFoundError, OSError, ValueError):
        return print('Could not load model data manifest.')

    # Check that models path exists and contains models
    if not move_to.is_dir():
        mkdir_full_perms(move_to)
    if not models_path.is_dir() or not os.listdir(models_path):
        return print('No models found!')
    logger = getLogger()

    # Create a dictionary of model names mapped to their sha256
    for name, data in models.items():
        for sha, url in data['resources'].items():
            if sha not in hashes:
                hashes[sha] = name

    # Check each file in the models directory for a matching sha256
    for p in [
        Path(models_path, n) for n in os.listdir(models_path)
        if Path(models_path, n).is_file() and n.endswith('.pth')
    ]:
        sha = get_sha256(p)
        if sha in hashes:
            name_from, name_to = p.name, f'{hashes[sha]}.pth'
            try:
                if name_from != name_to:
                    os.rename(p, p.with_name(name_to))
                    logger.info(f'{name_from}  -->  {name_to}')
            except FileExistsError:
                logger.error(f"Duplicate files: {name_from} | {name_to}")
        if sha not in hashes:
            logger.warning(f'UNRECOGNIZED: {p.name}')
            os.rename(p, Path(move_to, p.name))


def download_model(url: str, path: Path, chunk_size: int = 1024 * 1024 * 8) -> None:
    """Download a model in chunks.

    Args:
        url: URL where the model is hosted.
        path: Path to save the model.
        chunk_size: Amount of bytes to write on each stream iteration.
    """
    pbar = tqdm(total=0, unit='B', unit_scale=True, desc=f'[...] {path.stem}')

    def _update_progress(_url: str, _path: Path, current: int, total: int):
        """Updates the progress bar after each chunk written."""
        if pbar.total == 0:
            pbar.total = total
        pbar.update(current)

    # Download the file
    try:
        download_file(
            url=url,
            path=path,
            callback=_update_progress,
            chunk_size=chunk_size)

        # Download successful
        pbar.set_description(f'[SUCCESS] {path.stem}')
        return pbar.close()

    except Exception as e:
        # Download failed
        pbar.set_description(f'[FAILED] {path.stem} ({str(e)})')
        return pbar.close()


"""
* Retrieving Models
"""


def get_supported_models(
        models: dict[str, ManifestModel],
        tags: dict[str, OMDBTag],
        models_path: Path
) -> dict[str, ScalecordModel]:
    """Retrieve a mapping of currently installed and supported models, with display name as key.

    Args:
        models: Model data from the models manifest file.
        tags: Tag data from the tags manifest file.
        models_path: Path where `.pth` model files are installed.

    Returns:
        Formatted Scalecord model data mapped to their display name in discord.
    """
    supported_models: dict[str, ScalecordModel] = {}
    for name, model in models.items():

        # Check for a supported model
        model_path = (models_path / name).with_suffix('.pth')
        if not model_path.exists():
            continue

        # Format the supported model's non-implied tag names
        tags_found, implied = {}, []
        for tag in model['tags']:
            if tag not in tags:
                continue
            details = tags[tag]
            implied.extend(details.get('implies', []))
            tags_found[tag] = details['name']
        tag_names = [name for key, name in tags_found.items() if key not in implied]

        # Format the display name and check length
        display_name = f"[{model['scale']}X] {model['name']} ({', '.join(tag_names)})"
        while len(display_name) > 80:
            if tag_names:
                # Try with one less tag
                tag_names.pop()
                if tag_names:
                    display_name = f"[{model['scale']}X] {model['name']} ({', '.join(tag_names)})"
                    continue
                # Try with no tags
                display_name = f"[{model['scale']}X] {model['name']} (...)"
                continue
            # Trim the raw name
            display_name = f"[{model['scale']}X] {model['name']}"[:77]+'...'
            break

        # Add supported model
        supported_models[display_name] = ScalecordModel(
            architecture=model['architecture'],
            key=name,
            name=model['name'],
            path=model_path,
            resources=model['resources'],
            scale=model['scale'],
            tags=model['tags']
        )
    return supported_models
