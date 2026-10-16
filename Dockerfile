# One image runs the gateway, the admin API and the three MCP servers.
# Each Kubernetes Deployment picks its program with "command".
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY gateway ./gateway
COPY admin_api ./admin_api
COPY servers ./servers
COPY scripts/bootstrap.py ./scripts/bootstrap.py

# Run as a normal user, not root.
RUN useradd --uid 10001 --no-create-home app
USER 10001

ENV BIND_HOST=0.0.0.0
CMD ["python", "-m", "gateway.server"]
