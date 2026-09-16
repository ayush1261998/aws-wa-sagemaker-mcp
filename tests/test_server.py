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
# ruff: noqa: D101, D102, D103
"""Tests for the SageMaker Well-Architected MCP Server."""

import argparse
import pytest
from awslabs.sagemaker_wa_mcp_server.wa_validation_handler import WellArchitectedValidationHandler
from unittest.mock import MagicMock, patch


@pytest.mark.asyncio
async def test_server_initialization():
    from awslabs.sagemaker_wa_mcp_server.server import create_server

    server = create_server()

    assert server.name == 'awslabs.sagemaker-wa-mcp-server'
    assert server.instructions is not None
    assert 'SageMaker Well-Architected' in server.instructions
    assert 'pydantic' in server.dependencies
    assert 'loguru' in server.dependencies
    assert 'boto3' in server.dependencies


@pytest.mark.asyncio
async def test_server_initialization_streamable_http_sets_host_port():
    """streamable-http transport must bind 0.0.0.0:8000 in stateless mode per the
    Amazon Bedrock AgentCore Runtime MCP protocol contract."""
    from awslabs.sagemaker_wa_mcp_server.server import create_server

    server = create_server(transport='streamable-http')

    assert server.settings.host == '0.0.0.0'
    assert server.settings.port == 8000
    assert server.settings.stateless_http is True


@pytest.mark.asyncio
async def test_server_initialization_stdio_has_no_network_binding():
    """stdio transport (default/local use) must not set network-only settings."""
    from awslabs.sagemaker_wa_mcp_server.server import create_server

    server = create_server(transport='stdio')

    # FastMCP defaults host/port even when unused by stdio; the behavior we
    # guard is that stdio does NOT force stateless_http on, since that setting
    # only has meaning for HTTP transports.
    assert server.settings.stateless_http is False


@pytest.mark.asyncio
async def test_command_line_args_default():
    """Test default args (no sensitive data access)."""
    from awslabs.sagemaker_wa_mcp_server.server import main

    with patch.object(argparse.ArgumentParser, 'parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(
            allow_sensitive_data_access=False, transport='stdio'
        )

        mock_server = MagicMock()
        with patch(
            'awslabs.sagemaker_wa_mcp_server.server.create_server', return_value=mock_server
        ):
            with patch(
                'awslabs.sagemaker_wa_mcp_server.server.WellArchitectedValidationHandler'
            ) as mock_handler:
                main()

                mock_parse_args.assert_called_once()
                mock_handler.assert_called_once_with(mock_server, False)
                mock_server.run.assert_called_once_with(transport='stdio')


@pytest.mark.asyncio
async def test_command_line_args_sensitive_data():
    """Test with sensitive data access enabled."""
    from awslabs.sagemaker_wa_mcp_server.server import main

    with patch.object(argparse.ArgumentParser, 'parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(
            allow_sensitive_data_access=True, transport='stdio'
        )

        mock_server = MagicMock()
        with patch(
            'awslabs.sagemaker_wa_mcp_server.server.create_server', return_value=mock_server
        ):
            with patch(
                'awslabs.sagemaker_wa_mcp_server.server.WellArchitectedValidationHandler'
            ) as mock_handler:
                main()

                mock_handler.assert_called_once_with(mock_server, True)
                mock_server.run.assert_called_once_with(transport='stdio')


@pytest.mark.asyncio
async def test_command_line_args_streamable_http_transport():
    """Test that --transport streamable-http is passed through to create_server and run."""
    from awslabs.sagemaker_wa_mcp_server.server import main

    with patch.object(argparse.ArgumentParser, 'parse_args') as mock_parse_args:
        mock_parse_args.return_value = argparse.Namespace(
            allow_sensitive_data_access=False, transport='streamable-http'
        )

        mock_server = MagicMock()
        with patch(
            'awslabs.sagemaker_wa_mcp_server.server.create_server', return_value=mock_server
        ) as mock_create_server:
            with patch('awslabs.sagemaker_wa_mcp_server.server.WellArchitectedValidationHandler'):
                main()

                mock_create_server.assert_called_once_with(transport='streamable-http')
                mock_server.run.assert_called_once_with(transport='streamable-http')


@pytest.mark.asyncio
async def test_handler_tool_registration():
    """Test that all tools are registered on the MCP instance."""
    mock_mcp = MagicMock()

    WellArchitectedValidationHandler(mock_mcp)

    assert mock_mcp.tool.call_count == 5

    tool_names = [call[1]['name'] for call in mock_mcp.tool.call_args_list]
    assert 'validate_sagemaker_resource' in tool_names
    assert 'validate_all_endpoints' in tool_names
    assert 'validate_all_resources' in tool_names
    assert 'list_sagemaker_resources' in tool_names
    assert 'get_pillar_details' in tool_names
