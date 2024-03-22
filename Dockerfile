# Base image with CUDA support
FROM nvidia/cuda:12.3.2-base-ubuntu22.04

# Environment configuration
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND="noninteractive" \
    # User configuration
    DISCORD_BOT_TOKEN="" \
    DISCORD_GUILD_IDS="" \
    GITHUB_ACCESS_TOKEN="" \
    MAX_MODEL_SCALE=4 \
    MIN_COLORS_IN=3 \
    MIN_COLORS_OUT=3 \
    OWNER_ONLY=0 \
    # Poetry configuration
    POETRY_NO_INTERACTION=1

# Install system level dependencies
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    # Add the Deadsnakes PPA for Python 3.11
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        python3.11 \
        python3-pip \
        python3.11-venv \
        python3.11-dev && \
    # Set Python 3.11 as the default Python version
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --set python3 /usr/bin/python3.11 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --set python /usr/bin/python3.11 && \
    apt-get install -y --no-install-recommends pipx &&  \
    pipx ensurepath &&  \
    pipx install poetry &&  \
    # Clean up to keep the image size small
    apt-get clean &&  \
    rm -rf /var/lib/apt/lists/*

# Add poetry/pipx to PATH
ENV PATH="/root/.local/bin:${PATH}"

# Set the working directory
WORKDIR /app

# Copy project files
COPY poetry.lock pyproject.toml README.md ./

# Install dependencies
RUN poetry install --no-dev --no-root &&  \
    poetry cache clear pypi --all &&  \
    poetry cache clear pytorch --all &&  \
    poetry cache clear pytorch-xformers --all &&  \
    poetry cache clear torch --all &&  \
    pip cache purge

# Copy the rest of the application
COPY scalecord scalecord

# Install project scripts
RUN poetry install --only-root

# Command to run the application
CMD poetry run scalecord update data && \
    poetry run scalecord update models && \
    poetry run scalecord bot run
