# Scalecord
A discord bot which provides commands for upscaling images using PyTorch supported (`.pth`) models. Integrated with 
OpenModelDB to provide model metadata, automatically download models, and keep models and model data updated over time. 

## Requirements
- [Poetry](https://python-poetry.org/docs/)
- Python ^3.10
- An Nvidia GPU
- A discord [bot token](https://discord.com/developers/applications?new_application=true)

## Python Guide
1. Clone this repository somewhere on your system.
2. Install our requirements with `poetry install`.
3. In the `config` directory, duplicate the `dist.env.yml` file and rename it `env.yml`.
4. Create a bot by clicking the link above.
5. Invite it to your server via by going to "Oauth2" -> "URL Generator", generate a URL and navigate to it.
6. On the "Bot" page in your bot developer portal, click "Reset Token", copy that token. Paste it into the `env.yml` 
file for the `DISCORD_BOT_TOKEN` key. 
7. Fill in any additional optional values in the `env.yml`, remove any you don't wish to use.
8. Launch the bot using `poetry run scalecord`

## Docker Guide
Here's a boilerplate `docker-compose.yml` for the project:
```yaml
version: "3.8"
services:
  scalecord:
    image: investigamer/scalecord:latest
    container_name: scalecord
    environment:
      - DISCORD_BOT_TOKEN=your_bot_token_here
      - DISCORD_GUILD_IDS=your_server_id_here,another_server_id,comma_separated
      - GITHUB_ACCESS_TOKEN=github_access_token_optional
      # You may want this line for GPUs with less memory
      - PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
    ports:
      - "5000:5000"
    volumes:
      # Map a directory to each: app/cache, app/config, app/models
      - "C:/windows/path/to/cache:/app/cache"
      - "linux/path/to/config:/app/config"
      - "macos/path/to/models:/app/models"
    restart: unless-stopped
    # Below is required for upscaling with Nvidia GPU
    deploy:
      resources:
        reservations:
          devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

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

## How do I define custom models?
Duplicate the `dist.models.yml` file, rename it `models.yml`. Here you can define custom models sourced from 
wherever you prefer.

## Planned Features and Improvements
- A dockerized version of the app
- Wider support for automated model downloads
- More environment control, commands, settings, etc
- Manual metadata definitions for non-OMDB models
- More robust README and supporting documentation
- Support for AMD / CPU-only upscaling
- Support for NCNN / ONNX models
- ChaiNNer integration