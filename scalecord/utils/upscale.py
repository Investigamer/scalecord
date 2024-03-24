"""
* Utils: Upscale
"""
# Standard Library Imports
from contextlib import suppress
from datetime import datetime
import gc
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


class UpscaleChunkHandler:
    def __init__(
        self, model: ImageModelDescriptor,
        chunk: Image,
        logger: Logger,
        half_precision: bool = False
    ):
        # Remember core values
        self._tensor = None
        self._model = model
        self._chunk = chunk
        self._logger = logger or getLogger('discord')
        self._half_precision = half_precision

    async def __aenter__(self):
        """Enter the context manager."""

        # Convert the chunk to a tensor and await upscaling
        try:
            if self._half_precision:
                self._tensor = transforms.ToTensor()(self._chunk).cuda().unsqueeze(0).half()
            else:
                self._tensor = transforms.ToTensor()(self._chunk).cuda().unsqueeze(0)
            return self
        except Exception as e:

            # Retry at half precision
            if not self._half_precision:
                await self.clear_cache()
                self._half_precision = True
                self._logger.exception(
                    "Failed to create tensor for chunk, falling back to half precision.",
                    exc_info=e)

                # Create half precision tensor
                with suppress(Exception):
                    self._tensor = transforms.ToTensor()(self._chunk).cuda().unsqueeze(0).half()
                    return self

            # Upscale failed
            await self.clear_cache()
            self._logger.exception(
                "Failed to create tensor for chunk, even with half precision.",
                exc_info=e)
            return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Close the context manager."""
        self._model = None
        await self.clear_cache()

    """
    * Utility Methods
    """

    async def tensor_check(self) -> bool:
        """Checks that tensor was created successfully."""
        return bool(self._tensor is not None)

    async def upscale(self):
        """Upscale this chunk."""
        try:
            # Attempt to upscale image
            with torch.inference_mode():
                chunk = self._model(self._tensor).cpu()
            return chunk
        except Exception as e:

            # Retry at half precision
            if not self._half_precision:
                await self.clear_cache()
                self._half_precision = True
                self._logger.exception(
                    "Failed to upscale chunk with full precision tensor, falling back to half precision.",
                    exc_info=e)

                # Create half precision tensor
                with suppress(Exception):
                    self._tensor = transforms.ToTensor()(self._chunk).cuda().unsqueeze(0).half()
                    return await self.upscale()

            # Upscale failed
            self._logger.exception(
                "Failed to upscale chunk even at half precision.",
                exc_info=e)
            return None

    async def clear_cache(self):
        """Clears the Nvidia cache, removes model and tensor, collects garbage."""
        self._tensor = None
        torch.cuda.empty_cache()
        gc.collect()


class UpscaleHandler:
    def __init__(
        self, model: ImageModelDescriptor,
        image: Image,
        logger: Logger,
        half_precision: bool = False
    ):
        # Remember core values
        self._tensor = None
        self._model = model
        self._image = image
        self._logger = logger or getLogger('discord')
        self._half_precision = half_precision

    async def __aenter__(self):
        """Enter the context manager."""

        # Convert the chunk to a tensor and await upscaling
        try:
            if self._half_precision:
                self._tensor = transforms.ToTensor()(self._image).cuda().unsqueeze(0).half()
            else:
                self._tensor = transforms.ToTensor()(self._image).cuda().unsqueeze(0)
            return self
        except Exception as e:

            # Retry at half precision
            if not self._half_precision:
                await self.clear_cache()
                self._half_precision = True
                self._logger.exception(
                    "Failed to create tensor for image, falling back to half precision.",
                    exc_info=e)

                # Create half precision tensor
                with suppress(Exception):
                    self._tensor = transforms.ToTensor()(self._image).cuda().unsqueeze(0).half()
                    return self

            # Upscale failed
            await self.clear_cache()
            self._logger.exception(
                "Failed to create tensor for image, even with half precision.",
                exc_info=e)
            return self

    async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
        """Close the context manager."""
        self._model = None
        await self.clear_cache()

    """
    * Utility Methods
    """

    async def tensor_check(self) -> bool:
        """Checks that tensor was created successfully."""
        return bool(self._tensor is not None)

    async def upscale(self):
        """Upscale this image."""
        try:
            with torch.inference_mode():
                upscaled_image = self._model(self._tensor).cpu()
            return upscaled_image
        except Exception as e:

            # Retry at half precision
            if not self._half_precision:
                await self.clear_cache()
                self._logger.exception(
                    "Failed to upscale with full precision tensor, falling back to half precision.",
                    exc_info=e)

                # Create half precision tensor
                with suppress(Exception):
                    self._tensor = transforms.ToTensor()(self._image).cuda().unsqueeze(0).half()
                    return await self.upscale()

            # Upscale failed
            self._logger.exception(
                "Failed to upscale even at half precision.",
                exc_info=e)
            return None

    async def clear_cache(self):
        """Clears the Nvidia cache, removes model and tensor, collects garbage."""
        self._tensor = None
        torch.cuda.empty_cache()
        gc.collect()


"""
* Upscaling Images
"""


async def process_image_upscale(
    model_path: Path,
    image: Image,
    logger: Optional[Logger] = None,
    half_precision: bool = False,
    chunk_size: int = 512,
    chunk_threshold: int = 768
) -> Optional[Image]:
    """Upscales an image with optional half precision for memory optimization.

    Args:
        model_path: Path to a `.pth` model file used to upscale this image.
        image: PIL Image object to be upscaled.
        logger: Logger object used to pass logging information, uses `getLogger` if not provided.
        half_precision: Whether to reduce tensor to half precision to save memory.
        chunk_size: Size to use when splitting image into chunks for processing larger images.
        chunk_threshold: The max dimension allowed before an image is upscaled using chunked processing.

    Returns:
        PIL Image object upscaled by the provided model.
    """

    # Load the model
    model: Optional[ImageModelDescriptor] = ModelLoader().load_from_file(str(model_path))
    logger: Logger = logger or getLogger('discord')
    try:
        assert isinstance(model, ImageModelDescriptor)
    except AssertionError:
        logger.error(f'Model "{model_path.name}" is not supported.')
        return

    # Evaluate model and clear cache
    model.cuda().eval()
    if half_precision:
        model = model.half()
    torch.cuda.empty_cache()
    gc.collect()

    # Upscale image or with chunked processing
    upscaled_image = await upscale_image_chunks(
        model=model,
        image=image,
        logger=logger,
        half_precision=half_precision,
        chunk_size=chunk_size
    ) if any([n > chunk_threshold for n in image.size]) else await upscale_image(
        model=model,
        image=image,
        logger=logger,
        half_precision=half_precision)
    if not upscaled_image:
        return

    # Create our final Image object
    final_image = PIL.Image.fromarray(
        (upscaled_image.squeeze().permute(1, 2, 0).numpy() * 255)
        .astype(np.uint8))

    # Clear cuda cache and return the upscale
    del model, upscaled_image
    torch.cuda.empty_cache()
    gc.collect()
    return final_image


async def upscale_image_chunks(
    model: ImageModelDescriptor,
    image: Image,
    logger: Logger,
    half_precision: bool = False,
    chunk_size: int = 512
) -> Optional[torch.Tensor]:
    """Upscales a chunk of an image using the provided model asynchronously.

    Args:
        model: The PyTorch model used for upscaling.
        image: A PIL Image object representing a JPEG image.
        logger: Logger object used to pass logging information, uses `getLogger` if not provided.
        half_precision: Whether to use half precision for upscaling.
        chunk_size: Size to use for each chunk when splitting the image.

    Returns:
        A PyTorch tensor representing the upscaled chunk.
    """
    upscaled_chunks = []
    chunks = [
        image.crop((x, y, x + chunk_size, y + chunk_size))
        for y in range(0, image.height, chunk_size)
        for x in range(0, image.width, chunk_size)
    ]

    # Upscale each chunk using context manager
    for chunk in chunks:
        async with UpscaleChunkHandler(model=model, chunk=chunk, logger=logger, half_precision=half_precision) as ctx:
            if not await ctx.tensor_check():
                return logger.error('Failed to upscale one or more chunks.')
            upscaled_chunks.append(await ctx.upscale())

    # Check if chunks failed, otherwise combine chunks
    if any(n is None for n in upscaled_chunks):
        return logger.error("Failed to upscale one or more chunks of an image.")
    return torch.cat(upscaled_chunks, dim=0)


async def upscale_image(
    model: ImageModelDescriptor,
    image: Image,
    logger: Optional[Logger] = None,
    half_precision: bool = False
) -> Optional[Image]:
    """Upscales an image with optional half precision for memory optimization.

    Args:
        model: The PyTorch model used for upscaling.
        image: PIL Image object to be upscaled.
        logger: Logger object used to pass logging information, uses `getLogger` if not provided.
        half_precision: Whether to reduce tensor to half precision to save memory.

    Returns:
        PIL Image object upscaled by the provided model.
    """

    # Upscale image using context manager
    async with UpscaleHandler(
            model=model,
            image=image,
            logger=logger,
            half_precision=half_precision
    ) as ctx:
        if not await ctx.tensor_check():
            return logger.error('Failed to create tensor.')
        upscaled_image = await ctx.upscale()
    return upscaled_image
