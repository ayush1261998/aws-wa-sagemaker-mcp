# syntax=docker/dockerfile:1

# Amazon Bedrock AgentCore Runtime requires an ARM64 container listening on
# 0.0.0.0:8000 with a POST /mcp endpoint, using stateless streamable-HTTP.
# See: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp-protocol-contract.html
#
# Build for the required architecture explicitly, even on an x86 build host:
#   docker buildx build --platform linux/arm64 -t sagemaker-wa-mcp-server .

FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy only dependency manifests first so dependency installation is cached
# independently of application code changes.
COPY pyproject.toml uv.lock ./
COPY awslabs ./awslabs
COPY main.py README.md ./

# --frozen: fail rather than silently re-resolving if uv.lock is out of date.
# --no-dev: production image does not need ruff/pyright/pytest.
RUN uv sync --frozen --no-dev

EXPOSE 8000

# --transport streamable-http is the one flag that matters here: it is what
# makes this the AgentCore-compatible entrypoint (see server.py Phase 1
# transport switch). --allow-sensitive-data-access mirrors the default used
# in the documented local Kiro/Cursor/VS Code configs.
#
# Invoke the installed console-script directly (the venv uv sync created is
# at /app/.venv) rather than via `uv run`, which by default re-checks/syncs
# the environment on every invocation - unnecessary and reaches the network
# at container start for a production image that already has its deps baked
# in from the build step above.
ENTRYPOINT ["/app/.venv/bin/awslabs.sagemaker-wa-mcp-server", \
            "--transport", "streamable-http", \
            "--allow-sensitive-data-access"]
