"""
* Utils: Upscale
"""
# Standard Library Imports
from datetime import datetime
import gc
from logging import Logger, getLogger
from pathlib import Path
import socket
from typing import Optional, Union

# Third Party Imports
import numpy as np
from PIL.Image import Image
import torchvision.transforms
from spandrel import ImageModelDescriptor, ModelLoader, ModelTiling
import torch
from torch import Tensor

# Local Imports
from scalecord.utils.image import image_to_array, tensor_to_array, array_to_tensor, tensor_to_image

"""
* CUDA Utilities
"""


async def free_cuda_memory() -> None:
    """Safely clears the CUDA cache and frees up memory."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


"""
* Tensor Utilities
"""


def format_tensor_to_image(t: torch.Tensor) -> torch.Tensor:
    """Source: https://tinyurl.com/4u95r9xw"""
    if len(t.shape) == 2:
        # (H, W)
        return t
    elif len(t.shape) == 3:
        # (C, H, W) -> (H, W, C)
        return t.permute(1, 2, 0)
    elif len(t.shape) == 4:
        # (1, C, H, W) -> (H, W, C)
        return t.squeeze(0).permute(1, 2, 0)
    raise ValueError("Unsupported output tensor shape")


def format_tensor_to_batched(t: torch.Tensor) -> torch.Tensor:
    """Source: https://tinyurl.com/4u95r9xw"""
    if len(t.shape) == 2:
        # (H, W) -> (1, 1, H, W)
        return t.unsqueeze(0).unsqueeze(0)
    elif len(t.shape) == 3:
        # (H, W, C) -> (1, C, H, W)
        return t.permute(2, 0, 1).unsqueeze(0)
    raise ValueError("Unsupported input tensor shape")


def format_tensor_to_bgr(t: torch.Tensor) -> torch.Tensor:
    """Source: https://tinyurl.com/4u95r9xw"""
    if len(t.shape) == 3 and t.shape[2] == 3:
        # (H, W, C) RGB -> BGR
        return t.flip(2)
    elif len(t.shape) == 3 and t.shape[2] == 4:
        # (H, W, C) RGBA -> BGRA
        return torch.cat((t[:, :, 2:3], t[:, :, 1:2], t[:, :, 0:1], t[:, :, 3:4]), 2)
    return t


"""
* Context Managers
"""


class UpscaleHandler:
    """Context Manager class for gracefully handling a single image upscaling operation."""

    def __init__(
        self, model: ImageModelDescriptor,
        image: Union[Image, np.ndarray],
        logger: Logger
    ):
        # Set our starting values
        self._tensor = None
        self._model = model
        self._image = image
        self._logger = logger or getLogger('discord')

    """
    * Context Manager Methods
    """

    async def __aenter__(self):
        """Enter the context manager.

        Notes:
            - Clear the CUDA cache before proceeding.
            - Get a valid tensor object.
            - Return the context manager.
        """
        await free_cuda_memory()
        self._tensor = await self.get_tensor()
        return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Close the context manager."""
        self._tensor, self._model, self._image = None, None, None
        await free_cuda_memory()

    """
    * Utility Methods
    """

    async def tensor_check(self) -> bool:
        """Checks that tensor was created successfully."""
        return bool(self._tensor is not None)

    async def upscale(self) -> Optional[Union[Image, np.ndarray]]:
        """Upscale this image."""

        try:
            # Attempt to upscale image
            self._model.cuda()
            with torch.inference_mode():
                self._model.eval()
                output: Tensor = self._model(self._tensor)
            output = output.cpu().detach()

            # Convert to an image
            image = tensor_to_image(output)
            self._model.cpu()
            return image

        except Exception as e:
            # Upscaling the tensor failed (likely Out of Memory)
            return self._logger.exception("Failed to upscale image.", exc_info=e)

    async def upscale_tile(self) -> Optional[Union[Image, np.ndarray]]:
        """Upscale this image, treated as a tile."""

        try:
            # Attempt to upscale image
            self._model.cuda()
            with torch.inference_mode():
                self._model.eval()
                output: Tensor = self._model(self._tensor)
            output = output.cpu().detach()

            # Convert to array
            image_arr = tensor_to_array(output, as_tile=True)
            self._model.cpu()
            return image_arr

        except Exception as e:
            # Upscaling the tensor failed (likely Out of Memory)
            return self._logger.exception("Failed to upscale tile.", exc_info=e)

    async def get_tensor(self) -> Optional[torch.Tensor]:
        """Get tensor from image or tile."""
        try:
            # Compose a tensor
            if isinstance(self._image, Image):
                self._image = image_to_array(self._image)
            return array_to_tensor(self._image)
        except Exception as e:
            # Creating tensor failed (likely Out of Memory)
            return self._logger.exception(f"Failed to create tensor for chunk.", exc_info=e)


"""
* Processing Intermediaries
"""


async def process_image_upscale(
    model_path: Path,
    image: Image,
    logger: Optional[Logger] = None,
    tile_size: int = 512
) -> Optional[Image]:
    """Upscales an image with optional half precision for memory optimization.

    Args:
        model_path: Path to a `.pth` model file used to upscale this image.
        image: PIL Image object to be upscaled.
        logger: Logger object used to pass logging information, uses `getLogger` if not provided.
        tile_size: Size of tiles the image is broken into before upscaling, images below this size
            will be upscaled without tiling.

    Returns:
        PIL Image object upscaled by the provided model.
    """

    # Load the model
    logger: Logger = logger or getLogger('discord')
    model: Optional[ImageModelDescriptor] = ModelLoader().load_from_file(str(model_path))
    try:
        assert isinstance(model, ImageModelDescriptor)
    except AssertionError:
        return logger.error(f'Model "{model_path.name}" is not supported.')

    # Upscale image with tiled processing
    if max(image.size) > tile_size and model.tiling == ModelTiling.SUPPORTED:
        return await handle_tiled_image_upscale(
            model=model,
            image=image,
            logger=logger,
            tile_size=tile_size)

    # Upscale image
    return await handle_image_upscale(
        model=model,
        image=image,
        logger=logger)


"""
* Context Manager Intermediaries
"""


async def handle_tiled_image_upscale(
    model: ImageModelDescriptor,
    image: Image,
    logger: Optional[Logger],
    tile_size: int = 512
) -> Optional[Image]:
    """Upscales an image using a tiled approach, with a Context Manager.

    Args:
        model: The PyTorch model used for upscaling.
        image: A PIL Image object representing a loaded image.
        logger: Logger object used for backend output, use `getLogger` when not provided.
        tile_size: Max size of each tile to split the image by in each dimension.

    Returns:
        Upscaled image as a PIL Image object.
    """
    # Convert image to an array
    img_array: np.ndarray = image_to_array(image)
    upscaled_array = np.zeros(
        shape=(
            int(img_array.shape[0] * model.scale),
            int(img_array.shape[1] * model.scale),
            img_array.shape[2]
        ),
        dtype=np.uint8)

    # Split this image into tiles
    logger = logger or getLogger('discord')
    tiles = await get_tiles(
        image=img_array,
        tile_size=tile_size)

    # Upscale each tile
    for tile, x, y in tiles:

        # Upscale this tile
        async with UpscaleHandler(model=model, image=tile, logger=logger) as ctx:
            if not await ctx.tensor_check():
                logger.error('Unable to upscale tile.')
                return
            upscaled_tile = await ctx.upscale_tile()
            if upscaled_tile is None:
                logger.error('Unable to upscale tile.')
                return

        # Calculate the position of the upscaled tile
        upscaled_y = y * tile_size * model.scale
        upscaled_x = x * tile_size * model.scale

        # Place the upscaled tile into the upscaled image array
        upscaled_array[
            upscaled_y:(upscaled_y + upscaled_tile.shape[0]),
            upscaled_x:(upscaled_x + upscaled_tile.shape[1])
        ] = upscaled_tile

    # Return the upscaled image
    upscaled_tensor = torchvision.transforms.ToTensor()(upscaled_array)
    return torchvision.transforms.ToPILImage()(upscaled_tensor)


async def handle_image_upscale(
    model: ImageModelDescriptor,
    image: Image,
    logger: Optional[Logger] = None
) -> Optional[Image]:
    """Upscales an image with a Context Manager.

    Args:
        model: The PyTorch model used for upscaling.
        image: PIL Image object to be upscaled.
        logger: Logger object used to pass logging information, uses `getLogger` if not provided.

    Returns:
        Upscaled image as a PIL Image object.
    """
    async with UpscaleHandler(model=model, image=image, logger=logger) as ctx:
        if not await ctx.tensor_check():
            logger.error('Unable to upscale image.')
            return
        output = await ctx.upscale()
    return output


"""
* Tile Utilities
"""


async def get_tiles(image: np.ndarray, tile_size: int = 512) -> list[tuple[np.ndarray, int, int]]:
    """Gets a list of arrays representing image tiles from a PIL Image object based on a provided tile size.

    Args:
        image: PIL Image object to split into tiles.
        tile_size: Tile size used to calculate the number of tiles to generate.

    Returns:
        A list of tuples containing a tile array, an x coordinate, and a y coordinate. (tile, x, y)
    """

    # Calculate number of tiles for each dimension
    num_tiles_x = image.shape[1] // tile_size + (image.shape[1] % tile_size != 0)
    num_tiles_y = image.shape[0] // tile_size + (image.shape[0] % tile_size != 0)

    # Create a list of tiles
    return [
        (image[y * tile_size:(y + 1) * tile_size, x * tile_size:(x + 1) * tile_size], x, y)
        for y in range(num_tiles_y) for x in range(num_tiles_x)
    ]


"""
* Profiling
"""


class UpscaleProfilingHandler:
    """Context manager to profile torch CPU and CUDA resources during an upscale action."""

    def __init__(self):
        self._profile = None

    async def __aenter__(self):
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

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close the context manager."""
        self._profile.stop()

    @staticmethod
    def trace_ready(_profile):
        """Write trace."""
        host_name = socket.gethostname()
        timestamp = datetime.now().strftime("%b_%d_%H_%M_%S")
        file_prefix = f"{host_name}_{timestamp}"
        _profile.export_chrome_trace(f"{file_prefix}.json.gz")
        _profile.export_memory_timeline(f"{file_prefix}.html", device="cuda:0")
