# base image with uv
FROM ghcr.io/astral-sh/uv:0.4.9-python3.11-bookworm-slim

# Set the working directory
WORKDIR /app

# Copy the project into the container
COPY . /app

# Sync the project into a new environment using the frozen lockfile
RUN uv sync --frozen

# Run clippy
CMD ["uv", "run", "clippy", "--path", "/CLIP/"]
