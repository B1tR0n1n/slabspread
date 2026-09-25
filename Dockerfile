FROM python:3.12-slim
WORKDIR /srv
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv && uv pip install --system -e ".[postgres]" 2>/dev/null || true
COPY . .
RUN uv pip install --system -e ".[postgres]"
