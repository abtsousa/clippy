# base image with uv
FROM ghcr.io/astral-sh/uv:0.4.9-python3.11-bookworm-slim

# Copy the project into the container
COPY . /app

# Set the working directory
WORKDIR /app

# uv will install the project into .local/bin so we add it to the PATH
ENV PATH="$PATH:/root/.local/bin"

# Sync the project into a new environment using the frozen lockfile
RUN uv sync --frozen && \
uv tool install .

# Docker will launch clippy by default. You can override this by
# specifying a different command to run in the docker run <image> <command>.
CMD ["clippy", "--path", "/CLIP/"]
