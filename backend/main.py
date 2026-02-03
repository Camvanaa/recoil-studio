"""
Recoil Studio - 弹道配置生成器
后端主入口（同时托管前端静态文件）
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import pattern, lua

app = FastAPI(
    title="Recoil Studio API",
    description="弹道图识别和Lua配置生成服务",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(pattern.router, prefix="/api/pattern", tags=["弹道识别"])
app.include_router(lua.router, prefix="/api/lua", tags=["Lua生成"])

# 前端静态文件目录
FRONTEND_DIR = Path(__file__).parent / "static"

# 如果存在前端构建目录，则托管静态文件
if FRONTEND_DIR.exists():
    # 托管静态资源
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")
    
    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")
    
    @app.get("/{path:path}")
    async def serve_static(path: str):
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # SPA 回退到 index.html
        return FileResponse(FRONTEND_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "message": "Recoil Studio API",
            "version": "1.0.0",
            "note": "Frontend not built. Run 'npm run build' in frontend directory."
        }


@app.get("/health")
async def health():
    return {"status": "ok"}
