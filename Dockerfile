# 1. Use a lightweight Python base image
FROM python:3.12-slim

# 2. Copy the uv binary directly from Astral's official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Copy ONLY the dependency files first
# This is a Docker caching trick: if these don't change, Docker skips reinstalling
COPY pyproject.toml uv.lock ./

# 5. Install dependencies
# --frozen ensures uv uses the exact versions in uv.lock
# --no-install-project skips installing your actual source code for now
RUN uv sync --frozen --no-install-project --no-dev

# 6. Copy your actual project source code into the container
COPY . .

# 7. Install the project itself
RUN uv sync --frozen --no-dev

# 8. HOTFIX: Inject the missing SecretStr import into fastapi-mail
RUN sed -i '1s/^/from pydantic import SecretStr\n/' /app/.venv/lib/python3.12/site-packages/fastapi_mail/config.py

# 9. Define the command to run your app
# Replace "main.py" with the actual entry point of your application
CMD ["uv", "run", "fastapi", "run", "src/", "--host", "0.0.0.0", "--port", "8000"]