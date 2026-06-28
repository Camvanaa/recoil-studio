import pytest

from app.models.schemas import GunConfig, RecoilData
from app.patches import (
    Patch,
    PatchOperation,
    ProjectState,
    apply_patch,
    preview_patch,
    validate_patch,
)


def test_apply_patch_replaces_pattern_without_mutating_original_state():
    state = ProjectState(pattern=[RecoilData(y=1, x=2)])
    patch = Patch(
        id="replace",
        title="Replace pattern",
        operations=[
            PatchOperation(
                type="replace-pattern",
                target="pattern",
                value=[{"y": 10, "x": -2}],
            )
        ],
    )

    next_state = apply_patch(state, patch)

    assert [item.model_dump() for item in next_state.pattern] == [{"y": 10.0, "x": -2.0}]
    assert [item.model_dump() for item in state.pattern] == [{"y": 1.0, "x": 2.0}]


def test_apply_patch_transforms_pattern_axes():
    state = ProjectState(pattern=[RecoilData(y=10, x=-2), RecoilData(y=5, x=4)])
    patch = Patch(
        id="scale",
        title="Scale pattern",
        operations=[PatchOperation(type="transform-pattern", target="pattern", scale_y=2, scale_x=0.5)],
    )

    next_state = apply_patch(state, patch)

    assert [item.model_dump() for item in next_state.pattern] == [
        {"y": 20.0, "x": -1.0},
        {"y": 10.0, "x": 2.0},
    ]


def test_apply_patch_sets_sensitivity_and_gun_fields():
    state = ProjectState(guns=[GunConfig(name="AK", pattern=[RecoilData(y=1, x=1)])])
    patch = Patch(
        id="fields",
        title="Field patch",
        operations=[
            PatchOperation(type="set-field", target="sensitivity", path="mouse_sens", value=3.5),
            PatchOperation(type="set-field", target="gun", path="0.rpm", value=720),
        ],
    )

    next_state = apply_patch(state, patch)

    assert next_state.sensitivity.mouse_sens == 3.5
    assert next_state.guns[0].rpm == 720
    assert state.sensitivity.mouse_sens == 5
    assert state.guns[0].rpm == 600


def test_preview_patch_reports_before_and_after_values():
    state = ProjectState(pattern=[RecoilData(y=10, x=2)])
    patch = Patch(
        id="scale",
        title="Scale pattern",
        operations=[PatchOperation(type="transform-pattern", target="pattern", scale_y=2)],
    )

    preview = preview_patch(state, patch)

    assert preview.valid is True
    assert preview.changes[0].before == [{"y": 10.0, "x": 2.0}]
    assert preview.changes[0].after == [{"y": 20.0, "x": 2.0}]


def test_validate_patch_rejects_invalid_gun_path():
    state = ProjectState(guns=[])
    patch = Patch(
        id="bad",
        title="Bad patch",
        operations=[PatchOperation(type="set-field", target="gun", path="0.rpm", value=720)],
    )

    assert validate_patch(state, patch) == ["operations[0]: gun index out of range"]


def test_apply_patch_raises_for_invalid_patch():
    state = ProjectState()
    patch = Patch(id="bad", title="Bad patch", operations=[])

    with pytest.raises(ValueError, match="at least one operation"):
        apply_patch(state, patch)
