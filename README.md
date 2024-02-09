# Scalecord
A discord bot which provides commands for upscaling images using PyTorch supported (`.pth`) models. Integrated with 
OpenModelDB to provide model metadata, automatically download models, and keep models and model data updated over time. 

## Requirements
- [Poetry](https://python-poetry.org/docs/)
- Python ^3.10
- An Nvidia GPU
- A discord [bot token](https://discord.com/developers/applications?new_application=true)

## How to Install
1. Clone this repository somewhere on your system.
2. Install our requirements with `poetry install`.
3. In the `.config` directory, duplicate the `dist.env.yml` file and rename it `env.yml`.
4. Create a bot by clicking the link above.
5. Invite it to your server via by going to "Oauth2" -> "URL Generator", generate a URL and navigate to it.
6. On the "Bot" page in your bot developer portal, click "Reset Token", copy that token. Paste it into the `env.yml` 
file for the `DISCORD_BOT_TOKEN` key. 
7. Fill in any additional optional values in the `env.yml`, remove any you don't wish to use.
8. Launch the bot using `poetry run scalecord`

## How to Install (Docker)
We will be supporting a dockerized version soon.

## Where do I get models from?
[OpenModelDB](https://openmodeldb.info) is highly recommended since this app synchronizes tags and information for any models 
sourced from OpenModelDB. There is a command which will attempt to download all models from OpenModelDB after the 
bot has gathered the latest OpenModelDB data.
```bash
# To gather data
scalecord update data

# To download models
scalecord update models
```
Please note that currently this will only download models that have a valid direct URL. We plan to support downloading 
from other sources like Google Drive and Mega.nz in the future. Models not on OpenModelDB will need to provide any 
related metadata manually (docs pending).

## Planned Features and Improvements
- A dockerized version of the app
- Wider support for automated model downloads
- More environment control, commands, settings, etc
- Manual metadata definitions for non-OMDB models
- More robust README and supporting documentation
- Support for AMD / CPU-only upscaling
- Support for NCNN / ONNX models
- ChaiNNer integration