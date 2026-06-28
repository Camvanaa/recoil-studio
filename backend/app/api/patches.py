from fastapi import APIRouter, HTTPException

from app.patches import (
    Patch,
    PatchPreview,
    ProjectState,
    apply_patch,
    preview_patch,
    validate_patch,
)

router = APIRouter()


class PatchRequest(ProjectState):
    patch: Patch


@router.post("/validate", response_model=list[str])
async def validate_project_patch(request: PatchRequest):
    return validate_patch(request, request.patch)


@router.post("/preview", response_model=PatchPreview)
async def preview_project_patch(request: PatchRequest):
    return preview_patch(request, request.patch)


@router.post("/apply", response_model=ProjectState)
async def apply_project_patch(request: PatchRequest):
    try:
        return apply_patch(request, request.patch)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
