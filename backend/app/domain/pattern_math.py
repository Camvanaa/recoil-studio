from app.models.schemas import Point, RecoilData


def calculate_recoil_pattern(
    points: list[Point],
    scale_x: float = 1.0,
    scale_y: float = 1.0,
) -> list[RecoilData]:
    if len(points) < 2:
        return []

    pattern: list[RecoilData] = []
    for index in range(1, len(points)):
        prev = points[index - 1]
        curr = points[index]
        pattern.append(
            RecoilData(
                y=round((prev.y - curr.y) * scale_y, 6),
                x=round((prev.x - curr.x) * scale_x, 6),
            )
        )

    return pattern
