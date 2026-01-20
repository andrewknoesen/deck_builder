FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Ensure byte compilation and use copy instead of hardlink for UV (essential for Docker/Volumes)
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files
# Using monorepo context (build from root)
COPY pyproject.toml uv.lock ./
# Copy backend specific config if needed, or just rely on root
# We need to install the project dependencies. 
# Since 'backend' is a member, we might need the backend directory structure present if we wanted to install it editable,
# but 'uv sync' might just need pyproject.toml if we don't install root? 
# Actually, let's copy the backend directory to /app/backend to match structure expected by imports if running from root?
# No, usually we run from /app/backend.
# Let's assume we copy everything.

COPY . .

# Now sync. Since we have full source, 'uv sync' works.
RUN uv sync --frozen --no-install-project

# Expose port
EXPOSE 8000

# Command to run the application
# We need to point to existing app.
# If we are in /app, and we copied . ., then backend code is at /app/backend/app.
# So we should change WORKDIR to /app/backend or run uvicorn with full path.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

