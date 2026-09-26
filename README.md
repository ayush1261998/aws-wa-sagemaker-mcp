# Amazon SageMaker Well-Architected MCP Server

## Overview

The Amazon SageMaker Well-Architected MCP Server turns the AWS Well-Architected Framework into tools an AI agent runs against your live SageMaker workloads. Point it at an endpoint, training job, notebook instance, or model — or scan a whole region — and it returns prioritized findings and recommendations across all six pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability), using read-only AWS APIs.

## Use case

Teams running machine learning on SageMaker are expected to follow AWS best practices — encryption, VPC isolation, autoscaling, checkpointing, cost controls, and more — but reviewing each resource by hand is slow and easy to skip. This server lets an agent do that review on demand:

* **"Is this endpoint production-ready?"** — validate a single resource and get findings by severity, each with a recommended fix.
* **"Audit everything in this region."** — scan all endpoints (or all resource types) and get an aggregated HTML report.
* **"What does the Security pillar check?"** — list the checks behind any pillar.

**Benefits:**

* **50 checks across all six Well-Architected pillars.**
* **Read-only and safe** — only Describe / List / Get calls; no resource is modified.
* **Actionable** — every finding carries a severity and a recommendation.
* **Runs where you work** — locally in your IDE, or hosted on Amazon Bedrock AgentCore for shared/team access.

## Two ways to run

| | Local (IDE) | Hosted (AgentCore) |
|---|---|---|
| **How** | Your IDE spawns the server over stdio | A container running on Amazon Bedrock AgentCore Runtime |
| **Who can use it** | Only you, on that machine | Any authenticated caller with network access to the endpoint |
| **Credentials** | Your local AWS credentials | An IAM execution role attached to the runtime |
| **Best for** | Individual use, quick validation | Shared/team access, integration into a hosted agent |
| **Setup** | [Quickstart](#quickstart) below | [DEPLOYMENT.md](DEPLOYMENT.md) |

Local has no separate architecture — your IDE runs the process and it calls AWS with your credentials. The hosted path's reference architecture is at the top of [DEPLOYMENT.md](DEPLOYMENT.md).

## Available Features

### Well-Architected Validation

Provides comprehensive tools for validating SageMaker resources (endpoints, training jobs, notebook instances, and models) against AWS best practices across all six Well-Architected pillars. Each validation returns findings with severity levels and actionable recommendations. See the [validators documentation](awslabs/sagemaker_wa_mcp_server/README.md) for detailed information on the supported tools.

## Prerequisites

* [Install Python 3.10+](https://www.python.org/downloads/release/python-3100/)
* [Install the `uv` package manager](https://docs.astral.sh/uv/getting-started/installation/)
* [Install and configure the AWS CLI with credentials](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)

## Quickstart

This quickstart guide walks you through the steps to configure the Amazon SageMaker Well-Architected MCP Server for use with Kiro, Cursor, and other compatible IDEs.

| Kiro | Cursor | VS Code |
|:----:|:------:|:-------:|
| [![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=awslabs.sagemaker-wa-mcp-server&config=%7B%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22awslabs.sagemaker-wa-mcp-server%40latest%22%2C%22--allow-sensitive-data-access%22%5D%2C%22env%22%3A%7B%22FASTMCP_LOG_LEVEL%22%3A%22ERROR%22%7D%7D) | [![Install MCP Server](https://cursor.com/deeplink/mcp-install-light.svg)](https://cursor.com/en/install-mcp?name=awslabs.sagemaker-wa-mcp-server&config=eyJhdXRvQXBwcm92ZSI6W10sImRpc2FibGVkIjpmYWxzZSwiY29tbWFuZCI6InV2eCBhd3NsYWJzLnNhZ2VtYWtlci13YS1tY3Atc2VydmVyQGxhdGVzdCAtLWFsbG93LXNlbnNpdGl2ZS1kYXRhLWFjY2VzcyIsImVudiI6eyJGQVNUTUNQX0xPR19MRVZFTCI6IkVSUk9SIn0sInRyYW5zcG9ydFR5cGUiOiJzdGRpbyJ9) | [![Install on VS Code](https://img.shields.io/badge/Install_on-VS_Code-FF9900?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=SageMaker%20Well-Architected%20MCP%20Server&config=%7B%22autoApprove%22%3A%5B%5D%2C%22disabled%22%3Afalse%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22awslabs.sagemaker-wa-mcp-server%40latest%22%2C%22--allow-sensitive-data-access%22%5D%2C%22env%22%3A%7B%22FASTMCP_LOG_LEVEL%22%3A%22ERROR%22%7D%2C%22transportType%22%3A%22stdio%22%7D) |

**Set up Kiro**

See the [Kiro IDE documentation](https://kiro.dev/docs/mcp/configuration/) or the [Kiro CLI documentation](https://kiro.dev/docs/cli/mcp/configuration/) for details.

For global configuration, edit ~/.kiro/settings/mcp.json. For project-specific configuration, edit .kiro/settings/mcp.json in your project directory.

The example below includes the `--allow-sensitive-data-access` flag for accessing detailed resource configurations:

   **For Mac/Linux:**

	```
	{
	  "mcpServers": {
	    "awslabs.sagemaker-wa-mcp-server": {
	      "command": "uvx",
	      "args": [
	        "awslabs.sagemaker-wa-mcp-server@latest",
	        "--allow-sensitive-data-access"
	      ],
	      "env": {
	        "FASTMCP_LOG_LEVEL": "ERROR"
	      },
	      "autoApprove": [],
	      "disabled": false
	    }
	  }
	}
	```

   **For Windows:**

	```
	{
	  "mcpServers": {
	    "awslabs.sagemaker-wa-mcp-server": {
	      "command": "uvx",
	      "args": [
	        "--from",
	        "awslabs.sagemaker-wa-mcp-server@latest",
	        "awslabs.sagemaker-wa-mcp-server.exe",
	        "--allow-sensitive-data-access"
	      ],
	      "env": {
	        "FASTMCP_LOG_LEVEL": "ERROR"
	      },
	      "autoApprove": [],
	      "disabled": false
	    }
	  }
	}
	```

Verify your setup by running the `/tools` command in the Kiro CLI to see the available SageMaker Well-Architected MCP tools.

This server provides comprehensive Well-Architected validation for SageMaker workloads with 50 checks across all six pillars. For broader AWS API access and documentation lookup, you can also use [AWS API MCP Server](https://awslabs.github.io/mcp/servers/aws-api-mcp-server) and [AWS Documentation MCP Server](https://awslabs.github.io/mcp/servers/aws-documentation-mcp-server).

## Configurations

### Arguments

The `args` field in the MCP server definition specifies the command-line arguments passed to the server when it starts. These arguments control how the server is executed and configured. For example:

**For Mac/Linux:**
```
{
  "mcpServers": {
    "awslabs.sagemaker-wa-mcp-server": {
      "command": "uvx",
      "args": [
        "awslabs.sagemaker-wa-mcp-server@latest",
        "--allow-sensitive-data-access"
      ],
      "env": {
        "AWS_PROFILE": "your-profile",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

**For Windows:**
```
{
  "mcpServers": {
    "awslabs.sagemaker-wa-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "awslabs.sagemaker-wa-mcp-server@latest",
        "awslabs.sagemaker-wa-mcp-server.exe",
        "--allow-sensitive-data-access"
      ],
      "env": {
        "AWS_PROFILE": "your-profile",
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

#### Command Format

The command format differs between operating systems:

**For Mac/Linux:**
* `awslabs.sagemaker-wa-mcp-server@latest` - Specifies the latest package/version specifier for the MCP client config.

**For Windows:**
* `--from awslabs.sagemaker-wa-mcp-server@latest awslabs.sagemaker-wa-mcp-server.exe` - Windows requires the `--from` flag to specify the package and the `.exe` extension.

#### `--allow-sensitive-data-access` (optional)

Enables access to sensitive data such as detailed resource configurations, tags, and endpoint config details. This flag is required for tools that access potentially sensitive information.

* Default: true (Access to sensitive data is allowed by default)
* Example: remove `--allow-sensitive-data-access` from the `args` list in your MCP server definition to disable it.

### Environment variables

The `env` field in the MCP server definition allows you to configure environment variables that control the behavior of the SageMaker Well-Architected MCP server. For example:

```
{
  "mcpServers": {
    "awslabs.sagemaker-wa-mcp-server": {
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_PROFILE": "my-profile",
        "AWS_REGION": "us-west-2"
      }
    }
  }
}
```

#### `FASTMCP_LOG_LEVEL` (optional)

Sets the logging level verbosity for the server.

* Valid values: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
* Default: "WARNING"
* Example: `"FASTMCP_LOG_LEVEL": "ERROR"`

#### `AWS_PROFILE` (optional)

Specifies the AWS profile to use for authentication.

* Default: None (If not set, uses default AWS credentials).
* Example: `"AWS_PROFILE": "my-profile"`

#### `AWS_REGION` (optional)

Specifies the AWS region where SageMaker resources are validated, which will be used for all AWS service operations.

* Default: None (If not set, uses default AWS region).
* Example: `"AWS_REGION": "us-west-2"`

## Security & Permissions

### Features

The SageMaker Well-Architected MCP Server implements the following security features:

1. **AWS Authentication**: Uses AWS credentials from the environment for secure authentication.
2. **SSL Verification**: Enforces SSL verification for all AWS API calls.
3. **Least Privilege**: Only requires read/describe/list permissions on SageMaker resources.
4. **User Agent Tracking**: All API calls include a custom user agent for auditability.

### Considerations

When using the SageMaker Well-Architected MCP Server, consider the following:

* **AWS Credentials**: The server needs permission to describe and list SageMaker resources.
* **Network Security**: Ensure the environment running the server has network access to AWS APIs.
* **Authentication**: Use appropriate authentication mechanisms for AWS resources.
* **Authorization**: Configure IAM with read-only SageMaker permissions.
* **Data Protection**: Resource configurations may contain sensitive information.
* **Logging and Monitoring**: Enable logging and monitoring for SageMaker resources.

### Permissions

The SageMaker Well-Architected MCP Server performs only read-only operations, which is recommended and considered generally safe for production environments. Below are the tools available:

* **Read-only mode (default)**: `validate_sagemaker_resource`, `validate_all_endpoints`, `validate_all_resources`, `list_sagemaker_resources`, `get_pillar_details`.

#### `autoApprove` (optional)

An array within the MCP server definition that lists tool names to be automatically approved by the MCP Server client, bypassing user confirmation for those specific tools. Since all operations are read-only, auto-approving all tools is safe. For example:

**For Mac/Linux:**
```
{
  "mcpServers": {
    "awslabs.sagemaker-wa-mcp-server": {
      "command": "uvx",
      "args": [
        "awslabs.sagemaker-wa-mcp-server@latest"
      ],
      "env": {
        "AWS_PROFILE": "sagemaker-wa-mcp-readonly-profile",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "autoApprove": [
        "validate_sagemaker_resource",
        "validate_all_endpoints",
        "validate_all_resources",
        "list_sagemaker_resources",
        "get_pillar_details"
      ]
    }
  }
}
```

**For Windows:**
```
{
  "mcpServers": {
    "awslabs.sagemaker-wa-mcp-server": {
      "command": "uvx",
      "args": [
        "--from",
        "awslabs.sagemaker-wa-mcp-server@latest",
        "awslabs.sagemaker-wa-mcp-server.exe"
      ],
      "env": {
        "AWS_PROFILE": "sagemaker-wa-mcp-readonly-profile",
        "AWS_REGION": "us-east-1",
        "FASTMCP_LOG_LEVEL": "INFO"
      },
      "autoApprove": [
        "validate_sagemaker_resource",
        "validate_all_endpoints",
        "validate_all_resources",
        "list_sagemaker_resources",
        "get_pillar_details"
      ]
    }
  }
}
```

### Role Scoping Recommendations

In accordance with security best practices, we recommend the following:

1. **Create dedicated IAM roles** to be used by the SageMaker Well-Architected MCP Server with the principle of "least privilege."
2. **Use read-only roles** since the server only performs describe and list operations.
3. **Implement resource tagging** to limit actions to specific resources.
4. **Enable AWS CloudTrail** to audit all API calls made by the server.
5. **Regularly review** the permissions granted to the server's IAM role.
6. **Use IAM Access Analyzer** to identify unused permissions that can be removed.

### Sensitive Information Handling

**IMPORTANT**: Do not pass secrets or sensitive information via allowed input mechanisms:

* Do not include secrets or credentials in tool parameters.
* Do not pass sensitive information directly in the prompt to the model.
* Avoid using MCP tools for creating secrets, as this would require providing the secret data to the model.

**Instead of passing secrets through MCP**:

* Use AWS Secrets Manager or Parameter Store to store sensitive information.
* Configure proper IAM roles for service accounts.
* Use IAM roles for service accounts (IRSA) for AWS service access.

### File System Access

- **Read-Only Operations**: The server does not write to the file system or modify any AWS resources.
- **Host Credentials**: When run locally over stdio, the server uses the host's AWS credentials configuration. When deployed to Amazon Bedrock AgentCore Runtime, it uses the execution role attached to the runtime instead — see [DEPLOYMENT.md](DEPLOYMENT.md) for details.

## General Best Practices

* **Resource Naming**: Use descriptive names for SageMaker resources.
* **Error Handling**: Check for errors in tool responses and handle them appropriately.
* **Prioritize Findings**: Address HIGH severity findings first, then MEDIUM, then LOW.
* **Regular Audits**: Run validations periodically to catch configuration drift.
* **Monitoring**: Monitor resource status regularly.
* **Security**: Follow AWS security best practices for SageMaker resources.

## General Troubleshooting

* **Permission Errors**: Verify that your AWS credentials have the necessary read-only SageMaker permissions.
* **Resource Not Found**: Verify the resource name and region are correct.
* **SageMaker API Errors**: Verify that the SageMaker resources exist and are accessible.
* **Network Issues**: Check that the environment has network access to AWS APIs.
* **Client Errors**: Verify that the MCP client is configured correctly.
* **Log Level**: Increase the log level to DEBUG for more detailed logs.

For service-specific issues, consult the relevant documentation:
- [Amazon SageMaker AI Documentation](https://docs.aws.amazon.com/sagemaker/)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)

## Version

Current MCP server version: 0.1.0
