# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CDK app: deploy the SageMaker Well-Architected MCP Server to Amazon
Bedrock AgentCore Runtime.

Builds the repo's own Dockerfile (see ../Dockerfile) as a local asset,
pushes it to a CDK-managed ECR repository, and creates an AgentCore
Runtime configured for the MCP protocol with a scoped, read-only
execution role matching the AWS services this server's validators
actually call (see ../awslabs/sagemaker_wa_mcp_server/validators/).

Usage:
    cd cdk
    pip install -r requirements.txt
    cdk bootstrap   # one-time per account/region
    cdk deploy
"""

import os

from aws_cdk import App, CfnOutput, Stack
from aws_cdk import aws_bedrockagentcore as agentcore
from aws_cdk import aws_iam as iam
from constructs import Construct


# Read-only permissions matching the AWS services this server's validators
# actually call, verified against awslabs/sagemaker_wa_mcp_server/validators/
# and aws_helper.py (not the README's check catalog, which lists some
# checks - GuardDuty, Security Hub, IAM Access Analyzer - that are
# documented but not implemented in code).
EXECUTION_ROLE_STATEMENTS = [
    iam.PolicyStatement(
        sid='SageMakerReadOnly',
        actions=[
            'sagemaker:DescribeEndpoint',
            'sagemaker:DescribeEndpointConfig',
            'sagemaker:DescribeTrainingJob',
            'sagemaker:DescribeNotebookInstance',
            'sagemaker:DescribeModel',
            'sagemaker:ListEndpoints',
            'sagemaker:ListTrainingJobs',
            'sagemaker:ListNotebookInstances',
            'sagemaker:ListModels',
            'sagemaker:ListTags',
        ],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='CloudWatchMetricsAndAlarmsReadOnly',
        actions=[
            'cloudwatch:ListMetrics',
            'cloudwatch:DescribeAlarmsForMetric',
            'cloudwatch:GetMetricStatistics',
        ],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='CloudWatchLogsReadOnly',
        actions=['logs:DescribeLogGroups'],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='S3ReadOnly',
        actions=[
            's3:GetBucketEncryption',
            's3:GetBucketVersioning',
            's3:GetBucketReplication',
            's3:GetLifecycleConfiguration',
            's3:GetIntelligentTieringConfiguration',
        ],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='IamReadOnly',
        actions=['iam:ListAttachedRolePolicies'],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='Ec2NetworkingReadOnly',
        actions=[
            'ec2:DescribeSubnets',
            'ec2:DescribeVpcEndpoints',
            'ec2:DescribeFlowLogs',
        ],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='KmsReadOnly',
        actions=['kms:GetKeyRotationStatus'],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='CloudTrailReadOnly',
        actions=['cloudtrail:DescribeTrails', 'cloudtrail:GetTrailStatus'],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='ConfigReadOnly',
        actions=['config:DescribeConfigurationRecorderStatus'],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='ApplicationAutoScalingReadOnly',
        actions=[
            'application-autoscaling:DescribeScalableTargets',
            'application-autoscaling:DescribeScalingPolicies',
        ],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='ServiceQuotasReadOnly',
        actions=['servicequotas:GetServiceQuota'],
        resources=['*'],
    ),
    iam.PolicyStatement(
        sid='StsCallerIdentityReadOnly',
        actions=['sts:GetCallerIdentity'],
        resources=['*'],
    ),
]


class SageMakerWaMcpAgentCoreStack(Stack):
    """AgentCore Runtime deployment of the SageMaker WA MCP server."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        repo_root = os.path.join(os.path.dirname(__file__), '..')

        execution_role = iam.Role(
            self,
            'ExecutionRole',
            assumed_by=iam.ServicePrincipal('bedrock-agentcore.amazonaws.com'),
            description=(
                'Read-only execution role for the SageMaker Well-Architected '
                'MCP server on AgentCore Runtime. Grants only the describe/'
                'list/get actions the validators actually call - see '
                'awslabs/sagemaker_wa_mcp_server/validators/.'
            ),
        )
        for statement in EXECUTION_ROLE_STATEMENTS:
            execution_role.add_to_policy(statement)

        # Builds ../Dockerfile as a local asset; cdk deploy pushes it to a
        # CDK-managed ECR repository automatically.
        agent_runtime_artifact = agentcore.AgentRuntimeArtifact.from_asset(repo_root)

        runtime = agentcore.Runtime(
            self,
            'SageMakerWaMcpRuntime',
            runtime_name='sagemakerWaMcpServer',
            agent_runtime_artifact=agent_runtime_artifact,
            execution_role=execution_role,
            protocol_configuration=agentcore.ProtocolType.MCP,
            description='Amazon SageMaker Well-Architected MCP Server',
            # authorizer_configuration intentionally omitted: IAM
            # authentication (SigV4) is the default when unset, per the
            # aws_bedrockagentcore construct README.
        )

        CfnOutput(
            self,
            'AgentRuntimeArn',
            value=runtime.agent_runtime_arn,
            description='ARN of the deployed AgentCore Runtime',
        )


app = App()
SageMakerWaMcpAgentCoreStack(app, 'SageMakerWaMcpAgentCoreStack')
app.synth()
