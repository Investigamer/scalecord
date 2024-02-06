import os
from pathlib import Path
import random
import string
from threading import Lock
from time import perf_counter

from PIL import Image
from discord import Attachment, File, Client, app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord.interactions import Interaction

from scalecord._constants import models
from scalecord._autocomplete import model_autocomplete
from scalecord.utils.models import UpscaleModel
from scalecord.utils.properties import auto_prop_cached
from scalecord.utils.upscale import upscale_image


class UpscaleCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot: Bot = bot
        self.client: Client = bot

    @auto_prop_cached
    def render_lock(self) -> Lock:
        return Lock()

    @commands.is_owner()
    @app_commands.command(name='upscale', description="Upscale a provided image using a chosen model.")
    @app_commands.autocomplete(model_name=model_autocomplete)
    async def upscale_attached_image(self, ctx: type(Interaction), model_name: str, image: Attachment):

        # Load the selected model
        model: UpscaleModel = models.get(model_name)
        if not model:
            return await ctx.response.send_message(
                f'Sorry {ctx.user.mention}, I couldn\'t find a model named "{model_name}"!')
        await ctx.response.send_message(
            f"Request received {ctx.user.mention}!\n"
            f"Upscaling now, using model: `{model_name}`")

        # Load the image from the attachment
        image_in = Path(os.getcwd(), 'img', ''.join(random.choice(string.ascii_lowercase) for _ in range(16)))
        image_in = image_in.with_suffix(Path(image.filename).suffix)
        image_out = Path(os.getcwd(), 'out', image_in.name)
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
            content=f"Here you go, {ctx.user.mention}!\n"
                    f"**Upscale time:** `{time_completed}s`\n"
                    f"**Model used:** `{model_name}`\n"
                    f"**Dimensions:** `{dims_before}` **->** `{dims_after}`\n",
            attachments=[File(image_out)])
        os.remove(image_out)
