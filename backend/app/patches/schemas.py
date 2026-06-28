from typing import Literal

from pydantic import BaseModel, Field

from app.models.schemas import GunConfig, RecoilData, SensitivitySettings

PatchTarget = Literal["pattern", "gun", "sensitivity"]
PatchOperationType = Literal["replace-pattern", "set-field", "transform-pattern"]


class ProjectState(BaseModel):
    pattern: list[RecoilData] = Field(default_factory=list)
    guns: list[GunConfig] = Field(default_factory=list)
    sensitivity: SensitivitySettings = Field(default_factory=SensitivitySettings)


class PatchOperation(BaseModel):
    type: PatchOperationType
    target: PatchTarget
    path: str | None = None
    value: object | None = None
    scale_x: float | None = None
    scale_y: float | None = None


class Patch(BaseModel):
    id: str
    title: str
    operations: list[PatchOperation]


class PatchChange(BaseModel):
    operation: PatchOperation
    before: object | None
    after: object | None


class PatchPreview(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    changes: list[PatchChange] = Field(default_factory=list)
