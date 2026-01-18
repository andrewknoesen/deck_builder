FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Ensure byte compilation (optional)
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml .
COPY uv.lock .

# Install dependencies using UV
# --frozen ensures we stick to the lockfile
# --no-install-project avoids installing the current package itself if it's not needed as a library (we are running it as scripts)
# --system installs into the system python environment, or we can rely on .venv (default for uv sync).
# For simple docker images, installing into system or VIRTUAL_ENV is good.
# Using standard virtualenv approach:
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Sync dependencies
RUN uv sync --frozen --no-install-project

COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
# We use 'uv run' or just 'uvicorn' via the activated venv path
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
