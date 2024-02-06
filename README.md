# Scalecord
 An image upscaling bot for discord using PyTorch supported models from OpenModelDB.

## Requirements
- Python 3.10+
- [Poetry](https://python-poetry.org/docs/)
- An Nvidia GPU
- A discord [bot token](https://discord.com/developers/applications?new_application=true)

## How to Install
- Clone this repository somewhere on your system.
- Install our requirements with `poetry install`.
- In the `.config` directory, duplicate the `dist.env.yml` file and rename it `env.yml`.
- Create a bot by clicking the link above.
- Invite it to your server via:
  - Oauth2 -> URL Generator -> Visit link
- On the "Bot" page in your bot developer portal, click "Reset Token", copy that token.
Paste it into the `env.yml` for the `DISCORD_BOT_TOKEN` key. 
- Fill in any additional optional values in the `env.yml`, remove any you don't wish to use.
- Launch the bot using `poetry run scalecord`

# Adding Models
I recommend downloading models from [OpenModelDB](https://openmodeldb.info), place them in the `.models` folder

## Where do I get models from?
The [OpenModelDB](https://openmodeldb.info) is highly recommended since this app synchronizes tags and information for any models sourced from OpenModelDB.

## Planned Features and Improvements
- Automatic model downloading and updating
- More commands, more settings, etc
- A better README and documentation
- Support for AMD / CPU-only upscaling
- Support for NCNN / ONNX model files
- ChaiNNer integration