from app.domain.pattern_math import calculate_recoil_pattern
from app.models.schemas import Point


def test_calculate_recoil_pattern_domain_function():
    pattern = calculate_recoil_pattern(
        [Point(x=100, y=400), Point(x=95, y=375)],
        scale_x=1.5,
        scale_y=2,
    )

    assert [item.model_dump() for item in pattern] == [{"y": 50.0, "x": 7.5}]
