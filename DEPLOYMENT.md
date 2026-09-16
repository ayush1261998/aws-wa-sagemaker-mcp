# SageMaker Well-Architected MCP Server — AgentCore Deployment Guide

This guide covers deploying the SageMaker Well-Architected MCP server to
Amazon Bedrock AgentCore Runtime, so it runs as a hosted, network-reachable
service instead of a local process.

For running the server locally with an IDE (Kiro, Cursor, VS Code), see the
[main README](README.md) — that path is unchanged and does not require
anything in this guide.

## Local MCP vs. AgentCore Runtime — which do you need?

| | Local MCP (stdio) | AgentCore Runtime (this guide) |
|---|---|---|
| **Where it runs** | Spawned as a subprocess on your machine by your IDE | A managed container hosted by AWS, reachable over the network |
| **Who can use it** | Only you, on that machine | Any authenticated caller with network access to the endpoint |
| **AWS credentials** | Your local `~/.aws/credentials` / `AWS_PROFILE` | An IAM execution role attached to the runtime — no local credentials needed by callers |
| **Setup** | `uvx awslabs.sagemaker-wa-mcp-server` in your IDE's MCP config | Build a container, deploy an AgentCore Runtime resource (this guide) |
| **Best for** | Individual development, ad hoc validation | Shared/team access, no per-user AWS CLI setup, integration into a hosted agent |

If you only need the tools in your own IDE, use the [main README](README.md)
quickstart and stop here. Continue below only if you need the server
reachable over the network by other callers.

## Overview

The repository ships two deployment artifacts for this path:

* **`Dockerfile`** (repo root) — builds the MCP server as an ARM64 container
  that runs with `--transport streamable-http`, satisfying AgentCore
  Runtime's [MCP protocol contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp-protocol-contract.html):
  the container must listen on `0.0.0.0:8000` and expose `POST /mcp`.
* **`cdk/`** — an AWS CDK (Python) app that builds that Dockerfile as a CDK
  asset, creates a scoped IAM execution role, and deploys the AgentCore
  Runtime resource. This is the recommended path for a repeatable,
  version-controlled deployment.

## Security Best Practices

### Least privilege execution role

The CDK stack in this repo creates an execution role scoped to only the
read-only `Describe`/`List`/`Get` actions the validators call — matching
[`awslabs/sagemaker_wa_mcp_server/README.md`](awslabs/sagemaker_wa_mcp_server/README.md)'s
"AWS Services Used" table. It does **not** attach `ReadOnlyAccess` or any
broader managed policy. If you customize the execution role, start from
this scoped policy rather than widening it.

Most of the statements use `Resource: "*"` because the underlying IAM
actions (`sagemaker:ListEndpoints`, `cloudwatch:ListMetrics`,
`sts:GetCallerIdentity`, etc.) are account/region-level list-and-describe
operations that do not support resource-level ARN scoping — this is a
property of those AWS APIs, not a shortcut taken in this template.

### Authentication

By default, this stack omits `authorizerConfiguration`, so the runtime uses
**IAM (SigV4) authentication** — the default when unset. Callers must sign
requests with valid AWS credentials that are authorized to invoke the
runtime; the endpoint URL itself is not a secret. If you need callers
without AWS credentials (e.g., a third-party client), configure Cognito or
JWT authentication instead — see the
[`aws_bedrockagentcore` CDK construct reference](https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.aws_bedrockagentcore-readme.html#runtime-authentication-configuration)
for `RuntimeAuthorizerConfiguration.using_cognito()` / `.using_jwt()`.

### Network mode

The stack deploys in `PUBLIC` network mode (the AgentCore default) — the
runtime endpoint is internet-reachable but authentication-gated. For
workloads requiring network isolation, AgentCore Runtime also supports VPC
mode; see the CDK construct reference's "Runtime Network Configuration"
section.

### Credential separation

The execution role is completely separate from any local AWS credentials.
All AWS API calls the deployed server makes use the execution role you
specify — never credentials from whoever is calling the runtime.

### Scoping access per team or environment

Every caller that successfully authenticates against a deployed runtime
shares that runtime's execution role and AWS permissions. If different
teams or environments need different AWS access, deploy separate stacks
(each with its own execution role) rather than sharing one runtime across
them.

## Prerequisites

* An AWS account with permissions to create IAM roles, ECR repositories,
  and Bedrock AgentCore resources
* [AWS CDK Toolkit](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html) v2,
  compatible with `aws-cdk-lib>=2.269.0` (check with `cdk --version`; update
  with `npm install -g aws-cdk@latest` if needed)
* Python 3.10+ and `pip`
* Docker (or a Docker-compatible daemon, e.g. Colima) — CDK uses this to
  build the container image as part of `cdk deploy`
* AWS credentials configured locally (e.g. via `aws configure` or your
  organization's credential process) with permissions to deploy the stack

## Deploy

```bash
cd cdk
pip install -r requirements.txt

# One-time per AWS account/region:
cdk bootstrap aws://ACCOUNT_ID/REGION

cdk deploy
```

`cdk deploy` builds the repo's `Dockerfile` as a CDK asset, pushes it to a
CDK-managed ECR repository, creates the scoped execution role, and creates
the AgentCore Runtime. On success, it prints the deployed runtime's ARN as
a stack output:

```
Outputs:
SageMakerWaMcpAgentCoreStack.AgentRuntimeArn = arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:runtime/sagemakerWaMcpServer-XXXXXXXXXX
```

## Verify the deployment

Confirm the runtime reached `READY` status:

```bash
aws bedrock-agentcore-control get-agent-runtime \
  --agent-runtime-id sagemakerWaMcpServer-XXXXXXXXXX \
  --region REGION
```

## Invoke the deployed server

The runtime is invoked over streamable-HTTP at:

```
https://bedrock-agentcore.{region}.amazonaws.com/runtimes/{url-encoded-arn}/invocations?qualifier=DEFAULT
```

URL-encode the ARN by replacing `:` with `%3A` and `/` with `%2F`.

With IAM authentication (this stack's default), requests must be signed
with SigV4 using the `bedrock-agentcore` service name. Any AWS SDK's
request-signing utilities can do this; there is no separate bearer token to
manage. A minimal Python example using `botocore`:

```python
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

def sign_request(method, url, body, headers, region):
    credentials = boto3.Session().get_credentials()
    request = AWSRequest(method=method, url=url, data=body, headers=headers)
    SigV4Auth(credentials, 'bedrock-agentcore', region).add_auth(request)
    return dict(request.headers)
```

Send an `initialize` request first (the standard MCP handshake), capture
the returned `Mcp-Session-Id` header, and include it on subsequent
requests for session/microVM affinity — see
[MCP session management](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-mcp-protocol-contract.html#mcp-session-management-and-microvm-stickiness)
for details.

## Troubleshooting

**Tools not appearing / `AccessDenied` on tool calls** — check the
execution role's attached policy matches the services the resource you're
validating actually needs; see
[`awslabs/sagemaker_wa_mcp_server/README.md`](awslabs/sagemaker_wa_mcp_server/README.md)'s
service table. Use CloudTrail to confirm which role executed a given API
call.

**Connection refused / handshake fails** — confirm the runtime status is
`READY` (see Verify the deployment above), and that your request includes
a correctly URL-encoded runtime ARN and valid SigV4 signing.
