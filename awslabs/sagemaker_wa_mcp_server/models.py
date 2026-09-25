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

"""Data models for the SageMaker Well-Architected MCP Server.

These are the structured data shapes the validators and tools build. Tools
return their results as ``mcp.types.CallToolResult`` (human-readable text plus
``structuredContent``); these models describe the structured payload rather
than the MCP result envelope itself.
"""

from pydantic import BaseModel, Field
from typing import Optional


class Finding(BaseModel):
    """A single Well-Architected finding."""

    pillar: str = Field(..., description='Well-Architected pillar name')
    severity: str = Field(..., description='Severity level: HIGH, MEDIUM, or LOW')
    resource: str = Field(..., description='Resource name or identifier')
    check: str = Field(..., description='Check identifier')
    detail: str = Field(..., description='Description of the finding')
    recommendation: str = Field(..., description='Recommended remediation')


class PillarSummary(BaseModel):
    """Summary of findings for a single pillar."""

    HIGH: int = Field(0, description='Number of HIGH severity findings')
    MEDIUM: int = Field(0, description='Number of MEDIUM severity findings')
    LOW: int = Field(0, description='Number of LOW severity findings')


class ResourceSummary(BaseModel):
    """Summary of a SageMaker resource."""

    name: str = Field(..., description='Resource name')
    status: Optional[str] = Field(None, description='Resource status')


class PillarCheck(BaseModel):
    """Description of a single validation check."""

    id: str = Field(..., description='Check identifier')
    description: str = Field(..., description='What this check validates')
