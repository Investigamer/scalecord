"""
* Bot Command Groups
"""
# Standard Library Imports
import os
from itertools import islice
from pathlib import Path
import random
import string
from asyncio import Lock
from time import perf_counter

# Third Party Imports
from PIL import Image
from discord import Attachment, File, app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from omnitils.properties import default_prop

# Local Imports
from scalecord._constants import AppEnvironment
from scalecord.types.models import ScalecordModel
from scalecord.utils.upscale import process_image_upscale

"""
* Command Groups
"""


class UpscaleCog(commands.Cog):
    """Upscaling related command group."""

    def __init__(self, bot):
        super().__init__()
        self._bot: Bot = bot
        self._env: AppEnvironment = bot._env
        self._models = self._env.MODELS
        self.upscale_attached_image = app_commands.autocomplete(
            model_name=self.model_autocomplete
        )(self.upscale_attached_image)

    @default_prop
    def model_names(self) -> list[str]:
        return sorted([k for k in self._models.keys()])

    @default_prop
    def render_lock(self) -> Lock:
        return Lock()

    @commands.has_permissions(send_messages=True)
    @app_commands.command(name='upscale', description="Upscale a provided image using a chosen model.")
    async def upscale_attached_image(self, ctx: type(Interaction), model_name: str, image: Attachment):

        # Ensure image is valid
        if any([bool(not n) for n in [image.height, image.width]]):
            # Image not supplied
            return await ctx.response.send_message(
                f'Sorry {ctx.user.mention}, the attachment you provided is not a valid image!')
        if any([bool(n > 2000) for n in [image.height, image.width]]):
            # Todo: Create max dimensions environment variable
            # Image is too large
            return await ctx.response.send_message(
                f'Sorry {ctx.user.mention}, the image you provided was too big!\n'
                f'Right now we support upscaling images **2000px or smaller** (height or width).')

        # Load the selected model
        model: ScalecordModel = self._models.get(model_name)
        if not model:
            return await ctx.response.send_message(
                f'Sorry {ctx.user.mention}, I couldn\'t find a model named "{model_name}"!')

        # Establish model display info
        display_name = f"`[{model['scale']}X] {model['name']}`"
        display_arch = f"`{self._env.ARCHITECTURES[model['architecture']]}`"
        display_tags = ', '.join([
            f"`{self._env.TAGS[n]['name']}`" for n in model['tags']
        ])

        # Alert the user upscale is starting
        await ctx.response.send_message(
            f"I'm upscaling your image {ctx.user.mention}!\n"
            f"> **Model**: {display_name}\n"
            f"> **Tags**: {display_tags}\n"
            f"> **Architecture**: {display_arch}\n")

        # Load the image from the attachment
        rand_name = ''.join(random.choice(string.ascii_lowercase) for _ in range(16))
        image_in = Path(self._env.PATH_CACHE_IN, rand_name).with_suffix(Path(image.filename).suffix)
        image_out = Path(self._env.PATH_CACHE_OUT, image_in.name)
        await image.save(image_in)

        # Upscale and save the upscaled image
        async with self.render_lock:

            # Start timer and open image
            s = perf_counter()

            # Upscale the image
            with Image.open(image_in) as image:
                upscaled_image: Image = await process_image_upscale(
                    model_path=model['path'],
                    image=image,
                    logger=self._env.LOGR)

            # Alert the user if upscale failed, otherwise save the image
            if not upscaled_image:
                await ctx.edit_original_response(
                    content=f'Sorry {ctx.user.mention}, my GPU couldn\'t handle that image at the moment!')
                os.remove(image_in)
                return
            upscaled_image.save(image_out, optimize=True)

            # Check if image is small enough for Discord
            default_quality = 98
            while os.path.getsize(image_out) > (25 * 1024 * 1024):

                # Reduce quality on next iteration
                default_quality -= 1

                # If quality drops below 90%, alert the user and cancel
                if default_quality < 90:
                    await ctx.edit_original_response(
                        content=f'Hey {ctx.user.mention}, I managed to upscale your image. However, the result '
                                f'is too large to upload as an attachment! I tried to optimize the image as a JPEG and '
                                f'incrementally reduce the quality setting, but even at my configured minimum of 90% '
                                f'the file was just too darn big!\n'
                                f'\n'
                                f'Unfortunately Discord enforces a 25MB file attachment limit for bots like myself. '
                                f'Feel free to email the Discord support team and let them know how much you hate '
                                f'this obnoxiously low filesize limit.')
                    os.remove(image_in)
                    return

                # Remove old image, enforce JPEG filetype
                os.remove(image_out)
                if image_out.suffix != '.jpg':
                    image_out = image_out.with_suffix('.jpg')

                # Save as optimized JPEG with reduced quality
                upscaled_image.save(image_out, format='JPEG', quality=97, optimize=True)

            # Get before and after dimensions, then close the images
            dims_before = ' x '.join(str(n) for n in image.size)
            dims_after = ' x '.join(str(n) for n in upscaled_image.size)
            image.close(), upscaled_image.close()

            # Log time completed and delete the image
            time_completed = round(perf_counter()-s, 2)

        # Log to backend
        self._env.LOGR.info(
            f'[User: {ctx.user.name}] '
            f'Upscaled an image using {model["name"]}. '
            f'[{dims_before} -> {dims_after}]'
        )

        # Send the message, with the image attached
        await ctx.edit_original_response(
            content=f"That took me **{time_completed}** seconds!\n"
                    f"> **Model:** {display_name}\n"
                    f"> **Tags:** {display_tags}\n"
                    f"> **Dimensions:** `{dims_before}` **->** `{dims_after}`\n"
                    f"> **Architecture:** {display_arch}\n",
            attachments=[File(image_out)])

        # Remove images
        os.remove(image_out), os.remove(image_in)

    """
    * Autocomplete Methods
    """

    async def model_autocomplete(self, _ctx: Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Provides autocomplete results for model names.

        Args:
            _ctx: Context of the command interaction.
            current: The current string entered by the user for this command.

        Returns:
            Model choices the user can make.
        """
        # Generate a token list
        tokens = [t for t in current.lower().split(' ') if t] if current else []

        # If tokens provided, return top 25 matches
        if tokens:
            return list(islice(
                (
                    app_commands.Choice(name=n, value=n) for n in self.model_names
                    if all([bool(t in n.lower()) for t in tokens])
                ), 25
            ))

        # Return first 25 models
        return [app_commands.Choice(name=m, value=m) for m in self.model_names[:25]]
