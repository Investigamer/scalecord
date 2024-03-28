"""
* Image Utilities
"""
# Standard Library Imports
import gc
from pathlib import Path
from typing import Union

# Third Party Imports
import numpy as np
import PIL
import torchvision.transforms
from PIL.Image import Image
from torch import Tensor

"""
* Convert -> Tensor
"""


def array_to_tensor(img_array: np.ndarray) -> Tensor:
    """Takes in a Numpy array, turns it into a Tensor.

    Args:
        img_array: Numpy array representing an image.

    Returns:
        A Tensor object.
    """
    tensor = torchvision.transforms.ToTensor()(img_array)
    if tensor.shape != 4:
        tensor = tensor.unsqueeze(0)
    tensor = tensor.cuda()
    gc.collect()
    return tensor


def image_to_tensor(image: Image) -> Tensor:
    """Takes in a PIL Image object and converts it into a Tensor.

    Args:
        image: PIL Image object.

    Returns:
        A Tensor object.
    """
    img_array = image_to_array(image)
    return array_to_tensor(img_array)


"""
* Convert -> Array
"""


def image_to_array(image: Union[Path, Image]) -> np.array:
    """Takes in an image or path to an image and turns it into an array.

    Args:
        image: Path to the image or Image object.

    Returns:
        Numpy array.
    """
    # Provided as Image
    if isinstance(image, Image):
        return np.array(image)

    # Provided as path to image
    with PIL.Image.open(image) as img:
        arr = np.array(img)
    return arr


def tensor_to_array(tensor: Tensor, as_tile: bool = True) -> np.ndarray:
    """Takes in a Tensor, turns it into a Numpy array.

    Args:
        tensor: Tensor representing an upscaled image.
        as_tile: Whether to treat this tensor as a tile.

    Returns:
        A Numpy array.
    """
    if len(tensor.shape) == 4:
        tensor = tensor.squeeze(0)
    tensor = tensor.permute(1, 2, 0)
    if as_tile:
        tensor = tensor * 255
    tensor = tensor.numpy()
    tensor = tensor.astype(np.uint8)
    return tensor


"""
* Convert -> Image
"""


def array_to_image(img_array: np.ndarray) -> Image:
    """Takes in a Numpy array, turns it into a PIL Image object.

    Args:
        img_array: Numpy array representing an image.

    Returns:
        PIL Image object.
    """
    return PIL.Image.fromarray(img_array)


def tensor_to_image(tensor: Tensor) -> Image:
    """Takes in a Tensor, turns it into a PIL Image object.

    Args:
        tensor: Tensor representing an upscaled image.

    Returns:
        PIL Image object.
    """
    img_array = tensor_to_array(tensor)
    return array_to_image(img_array)
