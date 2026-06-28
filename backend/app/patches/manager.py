from copy import deepcopy

from app.models.schemas import RecoilData

from .schemas import Patch, PatchChange, PatchPreview, ProjectState


def validate_patch(state: ProjectState, patch: Patch) -> list[str]:
    errors: list[str] = []

    if not patch.operations:
        errors.append("patch must contain at least one operation")

    for index, operation in enumerate(patch.operations):
        prefix = f"operations[{index}]"
        if operation.type == "replace-pattern":
            if operation.target != "pattern":
                errors.append(f"{prefix}: replace-pattern target must be pattern")
            if not isinstance(operation.value, list):
                errors.append(f"{prefix}: replace-pattern value must be a list")
        elif operation.type == "transform-pattern":
            if operation.target != "pattern":
                errors.append(f"{prefix}: transform-pattern target must be pattern")
            if operation.scale_x is None and operation.scale_y is None:
                errors.append(f"{prefix}: transform-pattern requires scale_x or scale_y")
        elif operation.type == "set-field":
            errors.extend(_validate_set_field(state, prefix, operation.target, operation.path))
        else:
            errors.append(f"{prefix}: unsupported operation type {operation.type}")

    return errors


def preview_patch(state: ProjectState, patch: Patch) -> PatchPreview:
    errors = validate_patch(state, patch)
    if errors:
        return PatchPreview(valid=False, errors=errors)

    current = state.model_copy(deep=True)
    changes: list[PatchChange] = []

    for operation in patch.operations:
        before = _read_operation_value(current, operation)
        current = _apply_operation(current, operation)
        after = _read_operation_value(current, operation)
        changes.append(PatchChange(operation=operation, before=before, after=after))

    return PatchPreview(valid=True, changes=changes)


def apply_patch(state: ProjectState, patch: Patch) -> ProjectState:
    errors = validate_patch(state, patch)
    if errors:
        raise ValueError("; ".join(errors))

    next_state = state.model_copy(deep=True)
    for operation in patch.operations:
        next_state = _apply_operation(next_state, operation)
    return next_state


def _validate_set_field(
    state: ProjectState,
    prefix: str,
    target: str,
    path: str | None,
) -> list[str]:
    if not path:
        return [f"{prefix}: set-field requires path"]

    if target == "sensitivity":
        if not hasattr(state.sensitivity, path):
            return [f"{prefix}: unknown sensitivity field {path}"]
        return []

    if target == "gun":
        parts = path.split(".")
        if len(parts) != 2 or not parts[0].isdigit():
            return [f"{prefix}: gun path must be '<index>.<field>'"]
        gun_index = int(parts[0])
        if gun_index < 0 or gun_index >= len(state.guns):
            return [f"{prefix}: gun index out of range"]
        if not hasattr(state.guns[gun_index], parts[1]):
            return [f"{prefix}: unknown gun field {parts[1]}"]
        return []

    return [f"{prefix}: set-field target must be sensitivity or gun"]


def _apply_operation(state: ProjectState, operation) -> ProjectState:
    next_state = state.model_copy(deep=True)

    if operation.type == "replace-pattern":
        next_state.pattern = [RecoilData.model_validate(item) for item in operation.value]
        return next_state

    if operation.type == "transform-pattern":
        scale_x = operation.scale_x if operation.scale_x is not None else 1
        scale_y = operation.scale_y if operation.scale_y is not None else 1
        next_state.pattern = [
            RecoilData(y=round(item.y * scale_y, 6), x=round(item.x * scale_x, 6))
            for item in next_state.pattern
        ]
        return next_state

    if operation.type == "set-field" and operation.path:
        _set_field(next_state, operation.target, operation.path, operation.value)
        return next_state

    return next_state


def _read_operation_value(state: ProjectState, operation) -> object | None:
    if operation.type in {"replace-pattern", "transform-pattern"}:
        return [item.model_dump() for item in state.pattern]

    if operation.type == "set-field" and operation.path:
        return deepcopy(_get_field(state, operation.target, operation.path))

    return None


def _get_field(state: ProjectState, target: str, path: str) -> object:
    if target == "sensitivity":
        return getattr(state.sensitivity, path)

    gun_index, field = path.split(".")
    return getattr(state.guns[int(gun_index)], field)


def _set_field(state: ProjectState, target: str, path: str, value: object) -> None:
    if target == "sensitivity":
        setattr(state.sensitivity, path, value)
        return

    gun_index, field = path.split(".")
    setattr(state.guns[int(gun_index)], field, value)
