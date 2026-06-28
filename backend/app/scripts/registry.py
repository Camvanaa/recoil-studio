from typing import Protocol

from app.models.schemas import GunConfig, SensitivitySettings


class ScriptTarget(Protocol):
    id: str
    name: str

    def generate(self, guns: list[GunConfig], sensitivity: SensitivitySettings | None = None) -> str: ...


class ScriptTargetRegistry:
    def __init__(self):
        self._targets: dict[str, ScriptTarget] = {}

    def register(self, target: ScriptTarget) -> None:
        if target.id in self._targets:
            raise ValueError(f"script target already registered: {target.id}")
        self._targets[target.id] = target

    def get(self, target_id: str) -> ScriptTarget:
        try:
            return self._targets[target_id]
        except KeyError as error:
            raise KeyError(f"unknown script target: {target_id}") from error

    def list(self) -> list[ScriptTarget]:
        return list(self._targets.values())
