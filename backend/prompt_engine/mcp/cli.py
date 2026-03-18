from __future__ import annotations

from pathlib import Path

import typer

from prompt_engine.mcp.server import (
    DEFAULT_HTTP_HOST,
    DEFAULT_HTTP_PATH,
    DEFAULT_HTTP_PORT,
    build_cursor_http_config,
    build_cursor_stdio_config,
    build_mcp_server,
    dump_json,
)


app = typer.Typer(add_completion=False, no_args_is_help=True, help="Run Prompt Engine as an MCP server.")


@app.command("stdio")
def stdio(
    config_path: Path = typer.Option(Path("config/config.yaml"), "--config", help="Config file path."),
) -> None:
    server = build_mcp_server(config_path=config_path)
    server.run(transport="stdio")


@app.command("http")
def http(
    host: str = typer.Option(DEFAULT_HTTP_HOST, "--host", help="Bind host."),
    port: int = typer.Option(DEFAULT_HTTP_PORT, "--port", help="Bind port."),
    path: str = typer.Option(DEFAULT_HTTP_PATH, "--path", help="Streamable HTTP path."),
    config_path: Path = typer.Option(Path("config/config.yaml"), "--config", help="Config file path."),
) -> None:
    server = build_mcp_server(config_path=config_path, host=host, port=port, streamable_http_path=path)
    server.run(transport="streamable-http")


@app.command("cursor-config")
def cursor_config(
    transport: str = typer.Option("stdio", "--transport", help="One of: stdio, http."),
    url: str = typer.Option(
        f"http://{DEFAULT_HTTP_HOST}:{DEFAULT_HTTP_PORT}{DEFAULT_HTTP_PATH}",
        "--url",
        help="HTTP MCP endpoint when --transport http is used.",
    ),
    config_path: Path = typer.Option(Path("config/config.yaml"), "--config", help="Config file path."),
) -> None:
    if transport == "http":
        typer.echo(dump_json(build_cursor_http_config(url)))
        return
    typer.echo(dump_json(build_cursor_stdio_config(config_path)))


if __name__ == "__main__":
    app()
