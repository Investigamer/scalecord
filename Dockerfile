# Base image
FROM python:3.12-slim

# Install pipx
RUN python -m ensurepip --default-pip \
    && pip install --upgrade pip \
    && pip install pipx \
    && python -m pipx ensurepath \
    && pipx install poetry

# Set the working directory
WORKDIR /app

# Define build arguments for environment variables with default values
ARG DISCORD_BOT_TOKEN='token_string_here'
ARG DISCORD_GUILD_IDS=''
ARG GITHUB_ACCESS_TOKEN=''
ARG MAX_MODEL_SCALE=8
ARG MIN_COLORS_IN=3
ARG MIN_COLORS_OUT=3
ARG OWNER_ONLY=0

# Set environment variables using the ARG values
ENV DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
ENV DISCORD_GUILD_IDS=${DISCORD_GUILD_IDS}
ENV GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}
ENV MAX_MODEL_SCALE=${MAX_MODEL_SCALE}
ENV MIN_COLORS_IN=${MIN_COLORS_IN}
ENV MIN_COLORS_OUT=${MIN_COLORS_OUT}
ENV OWNER_ONLY=${OWNER_ONLY}

# Copy project files
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry install --no-dev --no-interaction

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["scalecord", "bot"]
