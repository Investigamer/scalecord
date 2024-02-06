"""
* Handle Autocompletion for Commands
"""
# Third Party Imports
from discord import Interaction
from discord.app_commands import Choice

# Local Imports
from scalecord._constants import models

"""
* Autocomplete Funcs
"""


async def model_autocomplete(_ctx: Interaction, current) -> list[Choice]:
    tokens = [n for n in current.split(' ') if n] if current else []
    if not tokens:
        return [
            Choice(name=k, value=k) for i, (k, v) in
            enumerate(models.items()) if
            v['type'] == '4x' and i < 25]
    return [
        Choice(name=k, value=k) for i, (k, v) in
        enumerate(models.items()) if
        all([n.lower() in k.lower() for n in tokens]) and i < 25]
