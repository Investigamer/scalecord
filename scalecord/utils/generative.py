"""
* Utils: Generative Models
"""
# Standard Library Imports
from os import PathLike
from typing import Optional, Union

# Third Party Imports
from diffusers import DiffusionPipeline
import torch

"""
* Stable Diffusion
"""


def stable_diffusion(
    prompt: str,
    path: Union[str, PathLike],
    dims: Optional[tuple[int, int]] = None,
    model_id: str = 'runwayml/stable-diffusion-v1-5',
    weights: Optional[tuple[str, str] | str] = None
) -> None:
    """Generate an image from a prompt using a stable diffusion model.

    Args:
        prompt: Prompt used to generate the image.
        path: Path to save the image.
        dims: Desired dimensions of the generated image, uses 1024 x 1024 if not provided.
        model_id: Model ID to use on huggingface. Will use the latest 'stable-diffusion' model by default.
        weights: Weights to use on huggingface, if provided.
    """

    # Create a pipeline
    pipeline = DiffusionPipeline.from_pretrained(model_id).to('cuda')
    if isinstance(weights, str):
        # Add weights as ID
        pipeline.load_lora_weights("e-n-v-y/envy-fantasy-art-deco-xl-01")
    if isinstance(weights, (tuple, list)):
        # Add weights as ID / name
        weights_id, weights_name = weights
        pipeline.load_lora_weights(weights_id, weight_name=weights_name)
    generator = torch.Generator("cuda").manual_seed(0)

    # Generate the image
    width, height = dims or (1024, 1024)
    image = pipeline(
        prompt,
        width=width,
        height=height,
        generator=generator
    ).images[0]

    # Save the image
    image.save(path)