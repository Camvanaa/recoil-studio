from app.models.schemas import Point
from app.services.pattern_detector import PatternDetector


def test_calculate_recoil_pattern_returns_empty_for_less_than_two_points():
    assert PatternDetector.calculate_recoil_pattern([]) == []
    assert PatternDetector.calculate_recoil_pattern([Point(x=10, y=20)]) == []


def test_calculate_recoil_pattern_uses_previous_minus_current_coordinates():
    points = [
        Point(x=100, y=400),
        Point(x=95, y=375),
        Point(x=110, y=350),
    ]

    pattern = PatternDetector.calculate_recoil_pattern(points)

    assert [item.model_dump() for item in pattern] == [
        {"y": 25.0, "x": 5.0},
        {"y": 25.0, "x": -15.0},
    ]


def test_calculate_recoil_pattern_applies_axis_scales():
    points = [
        Point(x=100, y=400),
        Point(x=98, y=390),
    ]

    pattern = PatternDetector.calculate_recoil_pattern(points, scale_x=1.5, scale_y=2.0)

    assert [item.model_dump() for item in pattern] == [{"y": 20.0, "x": 3.0}]


def test_calculate_recoil_pattern_rounds_to_six_decimals():
    points = [
        Point(x=10.0, y=10.0),
        Point(x=8.0 / 3.0, y=7.0 / 3.0),
    ]

    pattern = PatternDetector.calculate_recoil_pattern(points)

    assert pattern[0].y == 7.666667
    assert pattern[0].x == 7.333333


def test_calculate_recoil_pattern_returns_n_minus_one_steps():
    points = [
        Point(x=100, y=400),
        Point(x=100, y=390),
        Point(x=100, y=380),
        Point(x=100, y=370),
        Point(x=100, y=360),
        Point(x=100, y=350),
        Point(x=100, y=340),
        Point(x=100, y=330),
        Point(x=100, y=320),
        Point(x=100, y=310),
    ]

    pattern = PatternDetector.calculate_recoil_pattern(points)

    assert len(points) == 10
    assert len(pattern) == 9


def test_detect_from_multiple_bytes_aggregates_by_shot_index():
    detector = PatternDetector(min_dist=5)
    sample_a = [
        Point(x=100, y=300),
        Point(x=102, y=260),
        Point(x=104, y=220),
    ]
    sample_b = [
        Point(x=110, y=310),
        Point(x=112, y=270),
        Point(x=114, y=230),
    ]

    result = detector._cluster_shots_by_index(
        [
            type("Result", (), {"points": sample_a, "width": 0, "height": 0, "detection_mode": "target"})(),
            type("Result", (), {"points": sample_b, "width": 0, "height": 0, "detection_mode": "target"})(),
        ],
        3,
    )

    aggregated = [detector._average_points(group) for group in result]

    assert [point.model_dump() for point in aggregated] == [
        {"x": 105.0, "y": 305.0},
        {"x": 107.0, "y": 265.0},
        {"x": 109.0, "y": 225.0},
    ]
