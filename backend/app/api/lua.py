"""
Lua 生成 API
"""
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ..models.schemas import LuaGenerateRequest, LuaGenerateResponse
from ..services.lua_generator import LuaGenerator

router = APIRouter()


@router.post("/generate", response_model=LuaGenerateResponse)
async def generate_lua(request: LuaGenerateRequest):
    """
    根据枪械配置生成Lua脚本
    """
    try:
        if not request.guns:
            return LuaGenerateResponse(
                success=False,
                message="至少需要一个枪械配置",
                lua_code=""
            )
        
        lua_code = LuaGenerator.generate(request.guns)
        
        return LuaGenerateResponse(
            success=True,
            message=f"成功生成 {len(request.guns)} 把枪械的配置",
            lua_code=lua_code
        )
    
    except Exception as e:
        return LuaGenerateResponse(
            success=False,
            message=f"生成失败: {str(e)}",
            lua_code=""
        )


@router.post("/download")
async def download_lua(request: LuaGenerateRequest):
    """
    生成并下载Lua脚本文件
    """
    try:
        lua_code = LuaGenerator.generate(request.guns)
        
        return PlainTextResponse(
            content=lua_code,
            media_type="text/x-lua",
            headers={
                "Content-Disposition": "attachment; filename=macro-G502.lua"
            }
        )
    
    except Exception as e:
        return PlainTextResponse(
            content=f"-- 生成失败: {str(e)}",
            status_code=500
        )
