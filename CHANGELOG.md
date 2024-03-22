## 0.1.2 (2024-03-22)

### Fix

- **types**: Import NotRequired from typing_extensions to maintain Python 3.10 support

### Refactor

- **docker**: Slight docker cofiguration changes
- **cli**: Don't download existing models, add new commands to CLI group
- **cli**: Add upscale command to CLI
- **generative**: Initial test implementation of generative AI support with stable diffusion
- **profiler**: Add profiler context manager
- **constants**: Add user defined models to model library, ensure paths
- **commands**: Enforce valid images in upscale command, log upscales in the backend
- **docker**: Add docker instructions and Dockerfile, reconfigure project

## 0.1.1 (2024-02-08)

### Fix

- **_constants**: Allow comma separated string value for DISCORD_GUILD_IDS

## 0.1.0 (2024-02-08)

### Feat

- **cli**: Implement full CLI command support for launching, testing, and updating the app
- **types**: Add types module for defining types and data schemas for OpenModelDB and other model data objects

### Refactor

- **deprecations**: Remove deprecated modules, update JetBrains config
- **constants,client,commands**: Update environment intitialization and properties, implement environment handling and new autocomplete process for commands and the bot client
- **utils**: Remove utils provided by Omnitils, add and update utils for upscaling and model/model data handling
