from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from prompt_engine.mcp.server import build_mcp_server


def create_mcp_http_app(config_path: str | Path | None = None):
    server = build_mcp_server(config_path=config_path, streamable_http_path="/")
    return server.streamable_http_app()


def create_mcp_mount(config_path: str | Path | None = None):
    server = build_mcp_server(config_path=config_path, streamable_http_path="/")

    @asynccontextmanager
    async def lifespan(_app):
        async with server.session_manager.run():
            yield

    mount_app = server.streamable_http_app()
    mount_app.router.lifespan_context = lifespan
    return server, mount_app


app = create_mcp_http_app()
