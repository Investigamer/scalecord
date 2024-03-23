"""
* Image Utilities
"""
# Standard Library Imports
from io import BytesIO

# Third Party Imports
import PIL
from PIL.Image import Image


"""
* Conversions
"""


async def convert_to_jpg(image: Image) -> Image:
    """Converts a PIL image to jpg before upscaling to save memory.

    Args:
        image: PIL Image to convert to JPEG.

    Returns:
        Image object with JPEG format and RGB mode.
    """
    if image.format == 'JPEG':
        return image
    if image.mode != 'RGB':
        image = image.convert('RGB')
    buffer = BytesIO()
    image.save(buffer, format='JPEG', quality=97)
    image_jpg = PIL.Image.open(buffer)
    return image_jpg
