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

# Set default environment variables
ENV DISCORD_BOT_TOKEN=''
ENV DISCORD_GUILD_IDS=''
ENV GITHUB_ACCESS_TOKEN=''
ENV MAX_MODEL_SCALE=8
ENV MIN_COLORS_IN=3
ENV MIN_COLORS_OUT=3
ENV OWNER_ONLY=0

# Copy project files
COPY poetry.lock pyproject.toml ./

# Install dependencies
RUN poetry install --no-dev --no-interaction

# Copy the rest of the application
COPY . .

# Command to run the application
CMD ["scalecord", "bot"]
