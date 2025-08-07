"""Shared instance of langfuse client."""

import os

from langfuse import Langfuse
from rich.progress import Progress, SpinnerColumn, TextColumn



__all__ = ["langfuse_client"]



langfuse_client = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"), secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)


def flush_langfuse(client: "Langfuse | None" = None):
    """Flush shared LangFuse Client. Rich Progress included."""
    if client is None:
        client = langfuse_client

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Finalizing Langfuse annotations...", total=None)
        langfuse_client.flush()
