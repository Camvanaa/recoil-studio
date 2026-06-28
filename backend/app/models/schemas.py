"""
数据模型定义
"""
from typing import List, Literal

from pydantic import BaseModel, Field


class Point(BaseModel):
    """弹道点"""
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")


class RecoilData(BaseModel):
    """单发子弹的后坐力数据"""
    y: float = Field(..., description="垂直后坐力")
    x: float = Field(..., description="水平后坐力")


class PatternDetectRequest(BaseModel):
    """弹道识别请求参数"""
    scale_x: float = Field(default=1.0, description="X轴缩放倍率")
    scale_y: float = Field(default=1.0, description="Y轴缩放倍率")
    min_dist: int = Field(default=5, description="点之间最小距离")
    detection_mode: Literal["auto", "green", "target"] = Field(
        default="auto",
        description="识别模式：自动、官方绿点、靶场弹孔",
    )


class PatternDetectResponse(BaseModel):
    """弹道识别响应"""
    success: bool
    message: str
    points: List[Point] = Field(default_factory=list, description="识别到的弹孔点坐标")
    pattern: List[RecoilData] = Field(default_factory=list, description="计算出的补偿段数据")
    image_width: int = Field(default=0, description="图片宽度")
    image_height: int = Field(default=0, description="图片高度")
    shot_count: int = Field(default=0, description="识别到的弹孔数量")
    recoil_step_count: int = Field(default=0, description="相邻弹孔之间的补偿段数量")
    sample_count: int = Field(default=0, description="参与识别/聚合的样本数量")
    skipped_sample_count: int = Field(default=0, description="被跳过的无效样本数量")
    detection_mode: Literal["green", "target", "manual"] = Field(
        default="green",
        description="最终使用的识别模式",
    )


class GunConfig(BaseModel):
    """枪械配置"""
    name: str = Field(..., description="枪械名称")
    rpm: int = Field(default=600, description="每分钟射速")
    vertical_mul: float = Field(default=1.0, description="垂直倍率")
    horizontal_mul: float = Field(default=1.0, description="水平倍率")
    pattern: List[RecoilData] = Field(default_factory=list, description="补偿段数据")


class LuaGenerateRequest(BaseModel):
    """Lua生成请求"""
    guns: List[GunConfig] = Field(..., description="枪械配置列表")


class LuaGenerateResponse(BaseModel):
    """Lua生成响应"""
    success: bool
    message: str
    lua_code: str = Field(default="", description="生成的Lua代码")


class PatternUpdateRequest(BaseModel):
    """弹道更新请求（用于手动编辑）"""
    points: List[Point] = Field(..., description="更新后的点坐标")
    scale_x: float = Field(default=1.0, description="X轴缩放倍率")
    scale_y: float = Field(default=1.0, description="Y轴缩放倍率")
