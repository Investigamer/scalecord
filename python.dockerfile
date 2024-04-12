# Base image with CUDA support
FROM nvidia/cuda:12.4.1-base-ubuntu22.04

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
    # Paths
    LD_LIBRARY_PATH="/usr/local/nvidia/lib64:${LD_LIBRARY_PATH}" \
    PATH="/root/.local/bin:${PATH}"

# Set the working directory
WORKDIR /app

# Copy project requirements and files
COPY requirements.base.txt requirements.torch.txt /app/
ADD scalecord /app/scalecord

# Install and update system level dependencies
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    # Add the deadsnakes PPA and install Python 3.11
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update -y &&  \
    apt-get install -y --no-install-recommends \
        git \
        build-essential \
        python3.11 \
        python3-pip \
        python3.11-venv \
        python3.11-dev && \
    # Set Python 3.11 as default, upgrade pip
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --set python3 /usr/bin/python3.11 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --set python /usr/bin/python3.11 && \
    python -m pip install --upgrade pip && \
    # Install scalecord project
    pip install -r requirements.torch.txt && \
    pip install -r requirements.base.txt && \
    # Housekeeping to reduce image size
    apt-get clean &&  \
    rm -rf /var/lib/apt/lists/* && \
    pip cache purge && \
    # Build the command entrypoint and install it
    echo "#!/bin/bash" > scalecord.sh && \
    echo 'export PYTHONPATH="/app:$PYTHONPATH"' >> scalecord.sh && \
    echo 'python -m scalecord.cli "$@"' >> scalecord.sh && \
    chmod +x scalecord.sh && \
    mv scalecord.sh /usr/local/bin/scalecord

# Command entrypoint and default commands
ENTRYPOINT ["scalecord"]
CMD ["update", "all", "bot", "run"]