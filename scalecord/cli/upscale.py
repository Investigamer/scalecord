"""
* Commands: Upscale Group
"""
# Standard Library Imports
import asyncio

# Third Party Imports
import click
from PIL import Image

# Local Imports
from scalecord._constants import initialize_environment
from scalecord.utils import upscale

"""
* Commands
"""


@click.command(name='image')
@click.argument('image_path')
async def upscale_image(image_path: str):

    # Load model list
    env = initialize_environment()
    model_list = '\n'.join([f"[{i}] {k}" for i, k in enumerate(env.MODELS.keys())])

    # Choose a model
    choice = input(f'{model_list}\n'
                   'Choose a model ...\n').strip()
    while True:
        if choice.isdigit() and int(choice) < len(env.MODELS.keys()):
            try:
                model = list(env.MODELS.values())[int(choice)]
                break
            except IndexError:
                env.LOGR.error('Encountered an internal error with the model list!')
                return
        choice = input('Invalid choice! Try again ...')

    # Load the image from the attachment
    image_in = env.PATH_CACHE_IN / image_path
    image_out = env.PATH_CACHE_OUT / image_in.name

    # Upscale and save the upscaled image
    image = Image.open(image_in)
    upscaled_image = asyncio.run(
        upscale.process_image_upscale(
            model_path=model['path'],
            image=image,
            logger=env.LOGR))
    upscaled_image.save(image_out, quality=97)

    # Reply
    env.LOGR.info('Image upscaled!')


"""
* Command Group
"""


@click.group(
    name='upscale',
    commands={
        'image': upscale_image,
    },
    help='Commands that facilitate upscaling images.',
)
def UpscaleCLIGroup():
    """Test CLI group for running image upscaling tasks."""
    pass


# Export command group
__all__ = ['UpscaleCLIGroup']
