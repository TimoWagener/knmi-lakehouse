# Use a base image with Python and uv pre-installed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation for faster startup
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking
ENV UV_LINK_MODE=copy

# Install dependencies
# We use a cache mount to speed up subsequent builds
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . .

# Install the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Set DAGSTER_HOME
ENV DAGSTER_HOME=/app

# Create directory for dagster home (logs, etc) if strictly needed, 
# though usually we mount a volume or use DBs.
RUN mkdir -p /app/dagster_home

# Default command
CMD ["dagster", "webserver", "-h", "0.0.0.0", "-p", "3000"]
