"""
弹道识别 API
"""
from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional

from ..models.schemas import (
    PatternDetectResponse,
    PatternUpdateRequest,
    Point,
    RecoilData
)
from ..services.pattern_detector import PatternDetector

router = APIRouter()


@router.post("/detect", response_model=PatternDetectResponse)
async def detect_pattern(
    file: UploadFile = File(..., description="弹道图片"),
    scale_x: float = Form(default=1.0, description="X轴缩放倍率"),
    scale_y: float = Form(default=1.0, description="Y轴缩放倍率"),
    min_dist: int = Form(default=5, description="点之间最小距离")
):
    """
    从上传的弹道图中识别弹道点并计算后坐力数据
    """
    try:
        # 读取图片数据
        image_bytes = await file.read()
        
        # 识别弹道点
        detector = PatternDetector(min_dist=min_dist)
        points, width, height = detector.detect_from_bytes(image_bytes)
        
        # 计算后坐力数据
        pattern = PatternDetector.calculate_recoil_pattern(points, scale_x, scale_y)
        
        return PatternDetectResponse(
            success=True,
            message=f"识别到 {len(points)} 个弹道点",
            points=points,
            pattern=pattern,
            image_width=width,
            image_height=height
        )
    
    except Exception as e:
        return PatternDetectResponse(
            success=False,
            message=f"识别失败: {str(e)}",
            points=[],
            pattern=[]
        )


@router.post("/recalculate", response_model=PatternDetectResponse)
async def recalculate_pattern(request: PatternUpdateRequest):
    """
    根据手动编辑后的点重新计算后坐力数据
    """
    try:
        pattern = PatternDetector.calculate_recoil_pattern(
            request.points, 
            request.scale_x, 
            request.scale_y
        )
        
        return PatternDetectResponse(
            success=True,
            message=f"重新计算完成，共 {len(pattern)} 发弹道数据",
            points=request.points,
            pattern=pattern,
            image_width=0,
            image_height=0
        )
    
    except Exception as e:
        return PatternDetectResponse(
            success=False,
            message=f"计算失败: {str(e)}",
            points=[],
            pattern=[]
        )
