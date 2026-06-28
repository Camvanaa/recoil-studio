from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import data, lua, patches, pattern, tasks


def create_app(static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(
        title="Recoil Studio API",
        description="弹道图识别和Lua配置生成服务",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(pattern.router, prefix="/api/pattern", tags=["弹道识别"])
    app.include_router(lua.router, prefix="/api/lua", tags=["Lua生成"])
    app.include_router(patches.router, prefix="/api/patches", tags=["Patch管理"])
    app.include_router(tasks.router, prefix="/api/tasks", tags=["任务生命周期"])
    app.include_router(data.router, prefix="/api/data", tags=["弹道预设"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    frontend_dir = static_dir or Path(__file__).parents[2] / "static"
    if frontend_dir.exists():
        app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")

        @app.get("/")
        async def serve_index():
            return FileResponse(frontend_dir / "index.html")

        @app.get("/{path:path}")
        async def serve_static(path: str):
            file_path = frontend_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(frontend_dir / "index.html")
    else:

        @app.get("/")
        async def root():
            return {
                "message": "Recoil Studio API",
                "version": "1.0.0",
                "note": "Frontend not built. Run 'npm run build' in frontend directory.",
            }

    return app
