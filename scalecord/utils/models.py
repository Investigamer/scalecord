"""
* Utils: Models
"""
# Standard Library Imports
import os
import json
from pathlib import Path
from typing import TypedDict, Optional

import requests

# Local Imports
from scalecord._constants import ENV
from scalecord.utils.files import get_sha256, load_data_file, mkdir_full_perms
from scalecord.utils.github import download_directory_files

"""
* Types
"""

ModelTypes = ['1x', '2x', '4x', '8x']


class UpscaleModel(TypedDict):
    name: str
    path: Path
    type: str
    tags: list[str]


"""
* Caching Model Data
"""


def get_all_models() -> dict:
    """Gets all models from the `models.json` file.

    Returns:
        A dictionary containing all models with model name as key.
    """
    path = ENV.CWD / '.cache' / 'models.json'
    return load_data_file(path)


def format_model_data(data: dict) -> dict:
    """Formats model data retrieved from OpenModelDB to reduce filesize."""
    return data


def update_model_data() -> None:
    """Downloads the latest JSON manifest files for all models on OpenModelDB."""

    # Base values
    repo = 'OpenModelDB/open-model-database'
    path_models = ENV.PATH_CACHE / 'models.yml'

    # Cache metadata
    download_directory_files(
        repo=repo,
        repo_dir='data',
        path=ENV.PATH_CACHE,
        token=ENV.GITHUB_ACCESS_TOKEN)

    # Cache model data
    with requests.get('https://openmodeldb.info/api/v1/models.json') as r:
        data = format_model_data(r.json())
        with open(path_models, 'w', encoding='utf-8') as f:
            json.dump(data, f)


def audit_model_data() -> dict[Path, list[dict[str, str]]]:
    """Audits the latest JSON manifest files for all models. Removes manifest files
    for any unsupported models and generates a blacklist. Generates a whitelist for
    supported models."""
    # Todo: Finish this
    oddities: dict[Path, list[dict[str, str]]] = {}
    models = ENV.CWD / '.cache' / 'models.json'
    with models.open('r', encoding='utf-8') as f:
        data = json.load(f)
        for name, r in data.items():
            resources = [
                {'platform': r['platform'], 'type': r['type']}
                for r in data.get('resources', [])
                if all([n in r for n in ['platform', 'type']])
            ]
            if len(resources) < 1:
                continue
            elif len(resources) > 1:
                oddities[name] = resources.copy()
            elif resources[0]['platform'] != 'pytorch' or resources[0]['type'] != 'pth':
                oddities[name] = resources.copy()
    return oddities


def rename_existing_models():
    # Todo: Clean this up big time
    shas = {}
    path = ENV.CWD / '.models'
    move_to = path / 'unrecognized'
    if not move_to.is_dir():
        mkdir_full_perms(move_to)
    if not path.is_dir() or not os.listdir(path):
        print('No models found!')
    models = get_all_models()
    for name, data in models.items():
        for res in data['resources']:
            if 'sha256' not in res:
                print('=' * 120)
                print(f'NO SHA256 PROVIDED: {name}')
                print('=' * 120)
                continue
            if res['sha256'] not in shas:
                shas[res['sha256']] = name
    for p in [Path(path, n) for n in os.listdir(path)]:
        if p.is_dir():
            continue
        sha = get_sha256(p)
        if sha in shas:
            name_from, name_to = p.name, f'{shas[sha]}.pth'
            if name_from != name_to:
                os.rename(p, p.with_name(name_to))
                print(f'{name_from}  -->  {name_to}')
        if sha not in shas:
            print('='*120)
            print(f'UNRECOGNIZED FILE: {p.name}')
            print('='*120)
            os.rename(p, Path(move_to, p.name))


"""
Outdated Utility Funcs
"""
# Todo: Rework these


def get_model_details(path: Path, model_type: str, tags: Optional[list[str]] = None) -> tuple[str, UpscaleModel]:
    tags = tags if tags else []
    name_split = path.stem.split('[')
    name = name_split[0].strip()
    if len(name_split) > 1:
        tags.extend([n.strip(' ][') for n in name_split[1].split(',')])
    key = f'[{path.parent.name}] {name}'
    if tags:
        key += f' ({", ".join(tags)})'
    return key, UpscaleModel(
        name=name,
        path=path,
        type=model_type,
        tags=list(set(tags)))


def get_models() -> dict[str, UpscaleModel]:
    models: dict[str, UpscaleModel] = {}
    _root = Path(ENV.CWD, '.models')
    for p in [_root / n for n in os.listdir(_root)]:
        if not p.is_dir():
            continue
        if p.name not in ModelTypes:
            continue
        for subp in [p / n for n in os.listdir(p)]:
            model_type = subp.parent.name
            if not subp.is_dir():
                name, details = get_model_details(
                    path=subp,
                    model_type=model_type)
                models[name] = details
                continue
            for inner in [subp / n for n in os.listdir(subp)]:
                if not inner.is_dir():
                    continue
                name, details = get_model_details(
                    path=inner,
                    model_type=model_type,
                    tags=[inner.parent.name])
                models[name] = details
    return models
