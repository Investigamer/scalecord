"""
* Scalecord App
* An upscaling bot for Discord.
"""
# Local Imports
from scalecord.utils.models import rename_existing_models, update_model_data


def run():
    """Launch the bot."""
    update_model_data()
    rename_existing_models()


if __name__ == "__main__":
    run()
