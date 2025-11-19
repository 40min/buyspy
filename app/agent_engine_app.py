# Copyright 2025 Google LLC
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

# mypy: disable-error-code="attr-defined,arg-type"
import logging
import os
from typing import Any

import google.auth
import vertexai
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.cloud import logging as google_cloud_logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider, export
from vertexai.agent_engines.templates.adk import AdkApp

from app.agent import get_app
from app.app_utils.tracing import CloudTraceLoggingSpanExporter
from app.app_utils.typing import Feedback


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Set up logging and tracing for the agent engine app."""
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        provider = TracerProvider()
        processor = export.BatchSpanProcessor(
            CloudTraceLoggingSpanExporter(
                project_id=os.environ.get("GOOGLE_CLOUD_PROJECT")
            )
        )
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent.

        Extends the base operations to include feedback registration functionality.
        """
        operations = super().register_operations()
        operations[""] = [*operations.get("", []), "register_feedback"]
        return operations


def _create_agent_engine() -> AgentEngineApp:
    """Create and initialize the agent engine."""
    _, project_id = google.auth.default()
    vertexai.init(project=project_id, location="europe-north1")
    artifacts_bucket_name = os.environ.get("ARTIFACTS_BUCKET_NAME")
    return AgentEngineApp(
        app=get_app(),
        artifact_service_builder=lambda: GcsArtifactService(
            bucket_name=artifacts_bucket_name
        )
        if artifacts_bucket_name
        else InMemoryArtifactService(),
    )


# Lazy-loaded agent engine instance
_agent_engine: AgentEngineApp | None = None


def get_agent_engine() -> AgentEngineApp:
    """Get the lazy-loaded agent engine instance."""
    global _agent_engine
    if _agent_engine is None:
        _agent_engine = _create_agent_engine()
    return _agent_engine


# Keep backwards compatibility for existing code that expect this as a module-level variable
agent_engine = get_agent_engine
