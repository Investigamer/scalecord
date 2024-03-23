"""
* Utils: Upscale
"""
# Standard Library Imports
from datetime import datetime
from logging import Logger, getLogger
from pathlib import Path
import socket
from typing import Optional

# Third Party Imports
import numpy as np
import PIL
from PIL.Image import Image
from spandrel import ModelLoader, ImageModelDescriptor
import torchvision.transforms as transforms
import torch


"""
* Context Managers
"""


class ProfileUpscaleAction:
    """Context manager to profile torch CPU and CUDA resources during an upscale action."""

    def __init__(self):
        self._profile = None

    def __enter__(self):
        """Enter the context manager."""
        self._profile = torch.profiler.profile(
            activities=[
                torch.profiler.ProfilerActivity.CPU,
                torch.profiler.ProfilerActivity.CUDA
            ],
            schedule=torch.profiler.schedule(
                wait=0, warmup=0, active=6, repeat=1),
            record_shapes=True,
            profile_memory=True,
            with_stack=True,
            on_trace_ready=self.trace_ready
        )
        self._profile.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the context manager."""
        self._profile.stop()

    @staticmethod
    def trace_ready(self, _profile):
        """Write trace."""
        host_name = socket.gethostname()
        timestamp = datetime.now().strftime("%b_%d_%H_%M_%S")
        file_prefix = f"{host_name}_{timestamp}"
        _profile.export_chrome_trace(f"{file_prefix}.json.gz")
        _profile.export_memory_timeline(f"{file_prefix}.html", device="cuda:0")


"""
* Upscaling Images
"""


async def upscale_image(model_path: Path, image: Image, logger: Optional[Logger] = None) -> Optional[Image]:
    """Upscales an image.

    Args:
        model_path: Path to a `.pth` model file used to upscale this image.
        image: PIL Image object to be upscaled.
        logger: Logger object used to pass logging information, uses `getLogger` if not provided.

    Returns:
        PIL Image object upscaled by the provided model.
    """

    # Load the model
    model: ImageModelDescriptor = ModelLoader().load_from_file(str(model_path))
    try:
        assert isinstance(model, ImageModelDescriptor)
    except AssertionError:
        logger = logger or getLogger()
        logger.error(f'Model "{model_path.name}" is not supported.')
        return
    model.cuda().eval()

    # Load the image as a Tensor
    tensor = transforms.ToTensor()(image).cuda().unsqueeze(0)

    # Upscale the image
    with torch.no_grad():
        upscaled_image = model(tensor).cpu()
    del tensor

    # Convert the upscaled image to a PIL Image
    image_array = (upscaled_image.squeeze().permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    del upscaled_image

    # Clear cuda cache and return the upscale
    torch.cuda.empty_cache()
    return PIL.Image.fromarray(image_array)
