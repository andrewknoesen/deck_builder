ARG SKIP_COPY=false

FROM astral/uv:python3.13-bookworm-slim AS base

# Enable bytecode compilation and copy mode for mounted volumes
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure Python directory to be consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed
# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python version specified in .python-version
COPY .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv python install

# Copy dependency files
# Using monorepo context (build from root)
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    sh -c 'uv sync --frozen --no-dev --no-editable --package=mtg-deck-builder-backend'

FROM base AS copy-step-true
# Skipping copy steps when flag is passed

FROM base AS copy-step-false
COPY backend ./backend

FROM copy-step-${SKIP_COPY} AS final
ENV PATH="/app/.venv/bin:$PATH"

# Now sync. Since we have full source, 'uv sync' works.
RUN uv sync --frozen --no-install-project

# Expose port
EXPOSE 8000

# Command to run the application
# We need to point to existing app.
# If we are in /app, and we copied . ., then backend code is at /app/backend/app.
# So we should change WORKDIR to /app/backend or run uvicorn with full path.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

