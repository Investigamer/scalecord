"""
* Bot Client
"""
# Local Imports
from typing import Optional

# Third Party Imports
import discord
from discord.ext.commands import Bot

# Local Imports
from scalecord._constants import AppEnvironment
from scalecord._commands import UpscaleCog

"""
* Bot Client Class
"""


class BotClient(Bot):
    """Our main bot object."""

    def __init__(self, intents: Optional[discord.Intents], env: AppEnvironment):
        self._env = env

        # Establish priority guilds
        self.my_guilds = [discord.Object(id=i) for i in env.DISCORD_GUILD_IDS]
        super().__init__(command_prefix='/', intents=intents)

    """
    * Bot Hooks
    """

    async def setup_hook(self) -> None:
        """Called during bot setup."""

        # Add command groups
        upscale = UpscaleCog(self)
        await self.add_cog(upscale, guilds=self.my_guilds)

        # Sync command tree
        for guild in self.my_guilds:
            await self.tree.sync(guild=guild)
        await self.tree.sync()

    async def on_ready(self):
        """Called when bot is ready."""

        # Alert the bot has logged in
        print(f"Logged in as {self.user.name} (ID: {self.user.id})")
        print("=" * 120)


"""
* Bot Client Funcs
"""


def get_bot_client(env: AppEnvironment, intents: Optional[discord.Intents] = None):
    """Returns a BotClient instance."""
    if not intents:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.presences = True
    return BotClient(intents=intents, env=env)


def run_bot_client(
    env: AppEnvironment,
    intents: Optional[discord.Intents] = None
):
    """Create a BotClient instance, run it, and return it."""
    bot = get_bot_client(env, intents)
    bot.run(env.DISCORD_BOT_TOKEN)
    return bot
