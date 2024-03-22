"""
* Commands: Generate Group
"""
# Third Party Imports
import click

# Local Imports
from scalecord.utils.generative import stable_diffusion

"""
* Commands
"""


@click.command(name='image')
def generate_image():
    stable_diffusion(
        prompt="masterpiece, cute smiling tabby cat with big eyes, inside treasure room, "
               "best quality, warm lighting",
        path='img.jpg',
        dims=(1024, 1024),
        model_id="stabilityai/stable-diffusion-xl-base-1.0",
        weights="e-n-v-y/envy-fantasy-art-deco-xl-01"
    )


"""
* Command Group
"""


@click.group(
    name='generate',
    commands={
        'image': generate_image,
    },
    help='Commands that facilitate text to image generative AI tools like Stable Diffusion.',
)
def GenerateCLIGroup():
    """Test CLI group for running text to image generative AI tools like Stable Diffusion."""
    pass


# Export command group
__all__ = ['GenerateCLIGroup']
