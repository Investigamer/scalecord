"""
* Bot Command Groups
"""
# Standard Library Imports
import os
from itertools import islice
from pathlib import Path
import random
import string
from threading import Lock
from time import perf_counter

# Third Party Imports
from PIL import Image
from discord import Attachment, File, app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.interactions import Interaction
from omnitils.properties import default_property

# Local Imports
from scalecord._constants import AppEnvironment
from scalecord.types.models import ScalecordModel
from scalecord.utils.upscale import upscale_image

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

    @default_property
    def model_names(self) -> list[str]:
        return sorted([k for k in self._models.keys()])

    @default_property
    def render_lock(self) -> Lock:
        return Lock()

    @commands.has_permissions(send_messages=True)
    @app_commands.command(name='upscale', description="Upscale a provided image using a chosen model.")
    async def upscale_attached_image(self, ctx: type(Interaction), model_name: str, image: Attachment):

        # Load the selected model
        model: ScalecordModel = self._models.get(model_name)
        if not model:
            return await ctx.response.send_message(
                f'Sorry {ctx.user.mention}, I couldn\'t find a model named "{model_name}"!')

        # Establish model display info
        display_name = f"`[{model['scale']}X] {model['name']}`"
        display_arch = f"`{self._env.ARCHITECTURES[model['architecture']]}`"
        display_tags = ', '.join([
            f'`{self._env.TAGS[n]['name']}`' for n in model['tags']
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
        with self.render_lock:
            s = perf_counter()
            image = Image.open(image_in)
            dims_before = ' x '.join(str(n) for n in image.size)
            upscaled_image = upscale_image(model['path'], image)
            upscaled_image.save(image_out, quality=95)
            dims_after = ' x '.join(str(n) for n in upscaled_image.size)
            time_completed = round(perf_counter()-s, 2)
            os.remove(image_in)

        # Send the message, with the image attached
        await ctx.edit_original_response(
            content=f"That took me **{time_completed}** seconds!\n"
                    f"> **Model:** {display_name}\n"
                    f"> **Tags:** {display_tags}\n"
                    f"> **Dimensions:** `{dims_before}` **->** `{dims_after}`\n"
                    f"> **Architecture:** {display_arch}\n",
            attachments=[File(image_out)])
        os.remove(image_out)

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
