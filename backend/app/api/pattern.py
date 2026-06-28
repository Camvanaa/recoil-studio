"""
弹道识别 API
"""
from typing import Literal

from fastapi import APIRouter, File, Form, UploadFile

from ..models.schemas import (
    PatternDetectResponse,
    PatternUpdateRequest,
    Point,
    RecoilData
)
from ..services.pattern_detector import PatternDetector

router = APIRouter()


def _build_response(
    *,
    success: bool,
    message: str,
    points: list[Point] | None = None,
    pattern: list[RecoilData] | None = None,
    image_width: int = 0,
    image_height: int = 0,
    sample_count: int = 0,
    skipped_sample_count: int = 0,
    detection_mode: Literal["green", "target", "manual"] = "green",
) -> PatternDetectResponse:
    resolved_points = points or []
    resolved_pattern = pattern or []
    return PatternDetectResponse(
        success=success,
        message=message,
        points=resolved_points,
        pattern=resolved_pattern,
        image_width=image_width,
        image_height=image_height,
        shot_count=len(resolved_points),
        recoil_step_count=len(resolved_pattern),
        sample_count=sample_count,
        skipped_sample_count=skipped_sample_count,
        detection_mode=detection_mode,
    )


@router.post("/detect", response_model=PatternDetectResponse)
async def detect_pattern(
    file: UploadFile = File(..., description="弹道图片"),
    scale_x: float = Form(default=1.0, description="X轴缩放倍率"),
    scale_y: float = Form(default=1.0, description="Y轴缩放倍率"),
    min_dist: int = Form(default=5, description="点之间最小距离"),
    detection_mode: Literal["auto", "green", "target"] = Form(
        default="auto",
        description="识别模式：自动、官方绿点、靶场弹孔",
    ),
):
    """
    从上传的弹道图中识别弹道点并计算后坐力数据
    """
    try:
        image_bytes = await file.read()
        detector = PatternDetector(min_dist=min_dist)
        result = detector.detect_from_bytes(image_bytes, detection_mode=detection_mode)
        points = result.points
        width = result.width
        height = result.height
        pattern = PatternDetector.calculate_recoil_pattern(points, scale_x, scale_y)

        return _build_response(
            success=True,
            message=f"识别到 {len(points)} 个弹孔，生成 {len(pattern)} 段补偿",
            points=points,
            pattern=pattern,
            image_width=width,
            image_height=height,
            sample_count=1,
            detection_mode=result.detection_mode,
        )

    except Exception as e:
        return _build_response(
            success=False,
            message=f"识别失败: {str(e)}",
            detection_mode="green",
        )


@router.post("/detect-batch", response_model=PatternDetectResponse)
async def detect_pattern_batch(
    files: list[UploadFile] = File(..., description="多张靶场弹孔图片"),
    scale_x: float = Form(default=1.0, description="X轴缩放倍率"),
    scale_y: float = Form(default=1.0, description="Y轴缩放倍率"),
    min_dist: int = Form(default=5, description="点之间最小距离"),
    detection_mode: Literal["auto", "green", "target"] = Form(
        default="target",
        description="识别模式：自动、官方绿点、靶场弹孔",
    ),
):
    """
    从多张靶场图中识别弹孔并聚合为一条稳定弹道。
    """
    try:
        if len(files) < 2:
            raise ValueError("至少需要两张图片才能聚合弹道")

        image_bytes_list = [await file.read() for file in files]
        detector = PatternDetector(min_dist=min_dist)
        result = detector.detect_from_multiple_bytes(image_bytes_list, detection_mode=detection_mode)
        pattern = PatternDetector.calculate_recoil_pattern(result.points, scale_x, scale_y)

        return _build_response(
            success=True,
            message=(
                f"已聚合 {result.sample_count} 张样本，识别到 {len(result.points)} 个弹孔，"
                f"生成 {len(pattern)} 段补偿"
            ),
            points=result.points,
            pattern=pattern,
            image_width=result.width,
            image_height=result.height,
            sample_count=result.sample_count,
            skipped_sample_count=result.skipped_sample_count,
            detection_mode=result.detection_mode,
        )
    except Exception as e:
        return _build_response(
            success=False,
            message=f"聚合识别失败: {str(e)}",
            sample_count=len(files),
            detection_mode="target",
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
            message=f"重新计算完成，共 {len(request.points)} 个弹孔、{len(pattern)} 段补偿",
            points=request.points,
            pattern=pattern,
            image_width=0,
            image_height=0,
            shot_count=len(request.points),
            recoil_step_count=len(pattern),
            sample_count=1,
            skipped_sample_count=0,
            detection_mode="manual",
        )

    except Exception as e:
        return _build_response(
            success=False,
            message=f"计算失败: {str(e)}",
            detection_mode="manual",
        )
