# Phase 1 — AgentCore transport support

**Date:** 2026-09-15
**Status:** Complete, verified locally. No AWS/Isengard testing yet (Phase 2).
**Scope:** `awslabs/sagemaker_wa_mcp_server/server.py`, `tests/test_server.py`.
No changes to tool logic, validators, or the handler layer.

## Why

The repo owner asked for the server to be "easily consumable via local MCP
and also deployable to AgentCore." As shipped, the server only supported
**stdio transport** — `mcp.run()` with no arguments — which works for local
IDE use (Kiro, Cursor spawn the process and talk over stdin/stdout) but is
incompatible with Amazon Bedrock AgentCore Runtime.

AgentCore Runtime is a hosted environment: it cannot spawn a subprocess and
pipe stdin/stdout the way a local IDE does. Per AWS's MCP protocol contract
for AgentCore Runtime, it requires a network-reachable container that:

- Uses **streamable-http** transport (stateless mode recommended)
- Listens on host `0.0.0.0`, port `8000`
- Exposes `POST /mcp` as the RPC endpoint

Sources: [Deploy MCP servers in AgentCore Runtime](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp.html),
[MCP protocol contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp-protocol-contract.html).

## What changed

### `server.py`

1. **`create_server()` now accepts a `transport` argument** (default `'stdio'`).
   When `transport == 'streamable-http'`, it passes `host='0.0.0.0'`,
   `port=8000`, `stateless_http=True` to `FastMCP(...)`. For `stdio`, none of
   these are set — they have no meaning without a network binding.

2. **`main()` gained a new `--transport {stdio,streamable-http}` CLI flag**,
   default `stdio`. This is the switch a deployer picks at startup — the
   server itself never auto-detects its environment.

3. **`mcp.run()` now receives `transport=args.transport`** — the one line that
   actually changes runtime behavior.

Design choice: a flag with `stdio` as the default, rather than hardcoding
streamable-http, so every existing local Kiro/Cursor/VS Code config that
doesn't pass `--transport` keeps working with zero changes. One codebase
serves both consumption models; the deployer (a Kiro config locally, or a
future Dockerfile entrypoint for AgentCore) decides which mode at startup.

### `tests/test_server.py`

- Fixed 2 existing tests (`test_command_line_args_default`,
  `test_command_line_args_sensitive_data`) that hand-built an
  `argparse.Namespace` without a `transport` attribute — they now include
  `transport='stdio'` and assert `mcp.run.assert_called_once_with(transport='stdio')`.
- Added `test_command_line_args_streamable_http_transport` — asserts
  `--transport streamable-http` flows through to both `create_server()` and
  `mcp.run()`.
- Added `test_server_initialization_streamable_http_sets_host_port` — asserts
  `server.settings.host == '0.0.0.0'`, `.port == 8000`,
  `.stateless_http is True` when `transport='streamable-http'`.
- Added `test_server_initialization_stdio_has_no_network_binding` — asserts
  `stateless_http is False` for the default/stdio path (guards against the
  HTTP-only settings leaking into stdio mode).

## Verification performed

| Check | Method | Result |
|---|---|---|
| Full existing test suite | `uv run pytest tests/ -q` | 50 passed (45 original + 5 new/updated), 0 failed |
| `--help` output | `uv run python -m awslabs.sagemaker_wa_mcp_server.server --help` | `--transport {stdio,streamable-http}` shown, default stdio |
| stdio real MCP handshake | Scratch client using `mcp.client.stdio.stdio_client`, spawned the server exactly as an IDE would | Handshake OK, 5 tools discovered |
| streamable-http real MCP handshake | Started server with `--transport streamable-http`, scratch client using `mcp.client.streamable_http.streamablehttp_client` against `http://localhost:8000/mcp` | Handshake OK, same 5 tools discovered, server log shows clean `200 OK` on both the handshake and `tools/list` |

Both transports exposed the identical 5 tools:
`validate_sagemaker_resource`, `validate_all_endpoints`,
`validate_all_resources`, `list_sagemaker_resources`, `get_pillar_details`.

**Correction to initial repo review:** the server exposes **5 tools**, not
4 as originally documented in the top-level README's tool list. This should
be reconciled in the docs pass (Phase 5).

## What did NOT change

- No tool, validator, or `WellArchitectedValidationHandler` code was touched.
  The transport layer is fully decoupled from business logic — this was the
  point of the design, and the test results confirm the separation holds.
- No AWS API behavior was exercised in this phase — these tests only prove
  the MCP transport switch itself works. AWS credential flow and real
  SageMaker/CloudWatch/etc. calls are Phase 2 (requires Isengard).
- No Dockerfile / container work yet — that's Phase 3.

## Open items carried into later phases

- Phase 2: prove AWS access (boto3 credential chain) works identically in
  both transport modes using Isengard credentials — no code should need to
  change here, since credential resolution is untouched, but this needs to
  be demonstrated, not assumed.
- Phase 3: Dockerfile targeting `linux/arm64`, entrypoint running
  `--transport streamable-http`.
- Phase 4: AgentCore CLI scaffold + deploy + remote invocation test against
  Isengard.
- Phase 5: repo hygiene (LICENSE/NOTICE, CI, CONTRIBUTING) + fix the
  README's tool-count and `--allow-sensitive-data-access` default
  discrepancies + write the implementation guide (local vs. AgentCore
  sections) from what was actually verified above.


---

# Double-wrapped tool results fix

**Date:** 2026-09-25
**Scope:** `awslabs/sagemaker_wa_mcp_server/models.py`,
`awslabs/sagemaker_wa_mcp_server/wa_validation_handler.py`, `tests/test_server.py`.

## What changed

- Removed the custom `CallToolResult` base model (which shadowed
  `mcp.types.CallToolResult`) and the four response wrapper models
  (`ValidateResourceResponse`, `ValidateAllResponse`, `ListResourcesResponse`,
  `PillarInfoResponse`) from `models.py`. Kept the data models `Finding`,
  `PillarSummary`, `ResourceSummary`, `PillarCheck`.
- All five tools now return `mcp.types.CallToolResult` directly — the
  human-readable summary in `content`, the structured payload in
  `structuredContent` — via a new `_tool_result()` helper. Previously they
  returned the custom wrapper, which FastMCP re-serialized into the result
  text, nesting each tool response inside another.
- Added `test_tool_result_is_not_double_wrapped` to `tests/test_server.py`.

---

# DEPLOYMENT.md improvements

**Date:** 2026-09-25
**Scope:** `DEPLOYMENT.md`.

## What changed

- Prerequisites: stated the CDK CLI version floor (2.1141.0) with the
  `npx aws-cdk@latest` alternative; added `CDK_DOCKER` guidance for
  non-Docker builders; added an ARM64 emulation note.
- Deploy: added a virtualenv step, region guidance (`aws sts
  get-caller-identity`, same-region bootstrap, supported-regions link), and
  the IAM approval prompt (`cdk diff`, `--require-approval never`).
- Security: corrected the execution-role description to list the scoped
  operational permissions the AgentCore construct adds (CloudWatch Logs,
  X-Ray, `cloudwatch:PutMetricData`, ECR pull, workload identity).
- Verify: clarified the runtime ID and added `--query status`.
- Invoke: replaced the sign-only helper with a complete script that runs the
  full MCP sequence.
- Added an optional local container-test section and a `cdk destroy` cleanup
  section.


---

# README overview and reference architecture

**Date:** 2026-09-25
**Scope:** `README.md`, `DEPLOYMENT.md`, `.gitignore`.

## What changed

- `README.md`: added an Overview section, a Use case section, and a
  "Two ways to run" (local vs. AgentCore) comparison above the quickstart.
- `DEPLOYMENT.md`: added a reference architecture (Mermaid diagram plus a
  numbered walkthrough) at the top, describing the hosted AgentCore path.
- `.gitignore`: added `cdk.out/`.
