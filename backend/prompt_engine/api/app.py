from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from prompt_engine.api.rate_limit import RateLimitMiddleware
from prompt_engine.config import load_config
from prompt_engine.engine.optimizer import PromptOptimizationEngine
from prompt_engine.mcp.http import create_mcp_mount
from prompt_engine.models import OptimizeRequest, OptimizedPrompt, RunRequest, RunResponse


def create_app(config_path: str | None = None) -> FastAPI:
    config = load_config(config_path)
    engine = PromptOptimizationEngine(config)
    mcp_server, mcp_app = create_mcp_mount(config_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async with mcp_server.session_manager.run():
            yield

    app = FastAPI(title="Prompt Engine", version="0.1.3", lifespan=lifespan)
    app.state.engine = engine

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.security.allow_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RateLimitMiddleware, limit_per_minute=config.security.rate_limit_per_minute)
    app.mount("/mcp", mcp_app)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": config.environment}

    @app.post("/optimize", response_model=OptimizedPrompt)
    async def optimize(request: OptimizeRequest) -> OptimizedPrompt:
        return engine.optimize_prompt(request.prompt, request.context)

    @app.post("/run", response_model=RunResponse)
    async def run(request: RunRequest):
        if request.stream:
            optimized, output_stream = await engine.astream_run(
                request.prompt,
                provider=request.provider,
                model=request.model,
                context=request.context,
            )
            headers = {
                "x-prompt-intent": optimized.intent,
                "x-skills-applied": ",".join(optimized.skills_applied),
            }
            return StreamingResponse(output_stream, media_type="text/plain", headers=headers)

        return await engine.optimize_and_run_async(
            request.prompt,
            provider=request.provider,
            model=request.model,
            context=request.context,
        )

    @app.get("/metrics")
    async def metrics() -> Response:
        payload, content_type = engine.metrics.render()
        return Response(content=payload, media_type=content_type)

    return app


app = create_app()
