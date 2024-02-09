"""
* Utils: Models
"""
# Standard Library Imports
from pathlib import Path
from typing import TypedDict, NotRequired

"""
* Map Schemas
"""


class ModelManifestMap(TypedDict):
    """A mapping of required manifest resources to source URLs."""
    architectures: str
    models: str
    tag_categories: str
    tags: str


"""
* Model Architectures
"""


class OMDBArchitecture(TypedDict):
    """Object representing an OMDB model architecture."""
    compatiblePlatforms: list[str]
    input: str
    name: str


"""
* Model Tags
"""


class OMDBTagCategory(TypedDict):
    """Object representing an OMDB tag category."""
    description: str
    editOnly: NotRequired[bool]
    name: str
    order: int
    simple: bool
    tags: list[str]


class OMDBTag(TypedDict):
    """Object representing an OMDB tag."""
    description: str
    implies: list[str]
    name: str


"""
* Model Resources
"""


class ModelResource(TypedDict):
    """Object representing a model resource from a model manifest file."""
    platform: str
    type: str
    sha256: str
    size: int
    urls: list[str]


"""
* Model Images
"""


class ModelImageSize(TypedDict):
    """Object representing the size parameters of a model image asset from the OpenModelDB manifest."""
    width: int
    height: int


class ModelImage(TypedDict):
    """Object representing a model image asset from the OpenModelDB manifest."""
    type: str
    LR: NotRequired[str]
    SR: NotRequired[str]
    LRSize: NotRequired[ModelImageSize]
    SRSize: NotRequired[ModelImageSize]


"""
* Models
"""


class OMDBModel(TypedDict):
    """Object representing a model from the OpenModelDB `models.json` manifest."""
    architecture: str
    author: str
    dataset: NotRequired[str]
    datasetSize: NotRequired[int]
    date: str
    description: str
    images: list[ModelImage]
    inputChannels: int
    license: str
    name: str
    outputChannels: int
    pretrainedModelG: NotRequired[str]
    resources: list[ModelResource]
    scale: int
    size: list[str]
    tags: list[str]
    thumbnail: NotRequired[ModelImage]
    trainingBatchSize: NotRequired[int]
    trainingEpochs: NotRequired[int]
    trainingHRSize: NotRequired[int]
    trainingIterations: NotRequired[int]
    trainingOTF: NotRequired[bool]


class ManifestModel(TypedDict):
    """Object representing a model from a formatted manifest file."""
    architecture: str
    name: str
    resources: dict[str, list[str]]
    scale: int
    tags: list[str]


class ScalecordModel(TypedDict):
    """Object representing a supported PyTorch model."""
    architecture: str
    key: str
    name: str
    path: Path
    resources: dict[str, list[str]]
    scale: int
    tags: list[str]


"""
* Map Defaults
"""

ModelManifestMapDefaults = ModelManifestMap(
    architectures='https://openmodeldb.info/api/v1/architectures.json',
    models='https://openmodeldb.info/api/v1/models.json',
    tag_categories='https://raw.githubusercontent.com/OpenModelDB/open-model-database/main/data/tag-categories.json',
    tags='https://openmodeldb.info/api/v1/tags.json')
