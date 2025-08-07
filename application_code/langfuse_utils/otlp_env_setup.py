"""Set up environment variables for LangFuse integration."""

import base64
import logging
import os



def set_up_langfuse_otlp_env_vars():
    """Set up environment variables for Langfuse OpenTelemetry integration.

    OTLP = OpenTelemetry Protocol.

    This function updates environment variables.

    Also refer to:
    langfuse.com/docs/integrations/openaiagentssdk/openai-agents
    """

    langfuse_auth = base64.b64encode(
        f"{os.getenv("LANGFUSE_PUBLIC_KEY")}:{os.getenv("LANGFUSE_SECRET_KEY")}".encode()
    ).decode()

    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
        os.getenv("LANGFUSE_HOST") + "/api/public/otel"
    )
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"

    logging.info(f"Langfuse host: {os.getenv("LANGFUSE_HOST")}")
