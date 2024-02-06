"""
* Utils: Upscale
"""
# Standard Library Imports
from pathlib import Path

# Third Party Imports
import numpy as np
from PIL import Image
from spandrel import ModelLoader, ImageModelDescriptor
import torchvision.transforms as transforms
import torch

# Local Imports
from scalecord._constants import logger

"""
* Util Funcs
"""


def upscale_image(model_path: Path, image: Image) -> Image:
    """Upscales an image.

    Args:
        model_path: Path to a `.pth` model file used to upscale this image.
        image: PIL Image object to be upscaled.

    Returns:
        PIL Image object upscaled by the provided model.
    """

    # Load the model
    model: ImageModelDescriptor = ModelLoader().load_from_file(str(model_path))
    try:
        assert isinstance(model, ImageModelDescriptor)
    except AssertionError:
        logger.error(f'Model "{model_path.name}" is not supported.')
        return
    model.cuda().eval()

    # Load the image as a Tensor
    tensor = transforms.ToTensor()(image).cuda().unsqueeze(0)

    # Upscale the image
    with torch.no_grad():
        upscaled_image = model(tensor).cpu()
    image.close()

    # Convert the upscaled image to a PIL Image
    image_array = (upscaled_image.squeeze().permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    return Image.fromarray(image_array)
