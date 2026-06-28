from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.pattern import router
from app.models.schemas import Point, RecoilData
from app.services.pattern_detector import AggregateDetectionResult, DetectionResult, PatternDetector


app = FastAPI()
app.include_router(router, prefix="/api/pattern")
client = TestClient(app)


def test_detect_pattern_returns_shot_and_step_counts(monkeypatch):
    def fake_detect(self, image_bytes, detection_mode="auto"):
        return DetectionResult(
            points=[Point(x=100, y=300), Point(x=100, y=250), Point(x=105, y=200)],
            width=200,
            height=300,
            detection_mode="target",
        )

    monkeypatch.setattr(PatternDetector, "detect_from_bytes", fake_detect)

    response = client.post(
        "/api/pattern/detect",
        files={"file": ("target.png", b"fake", "image/png")},
        data={"detection_mode": "target"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["shot_count"] == 3
    assert body["recoil_step_count"] == 2
    assert body["sample_count"] == 1
    assert body["detection_mode"] == "target"
    assert body["pattern"] == [{"y": 50.0, "x": 0.0}, {"y": 50.0, "x": -5.0}]


def test_detect_pattern_batch_returns_aggregated_counts(monkeypatch):
    def fake_detect_many(self, images, detection_mode="target"):
        return AggregateDetectionResult(
            points=[Point(x=100, y=300), Point(x=102, y=250), Point(x=104, y=200)],
            width=220,
            height=360,
            detection_mode="target",
            sample_count=5,
            skipped_sample_count=1,
        )

    monkeypatch.setattr(PatternDetector, "detect_from_multiple_bytes", fake_detect_many)

    response = client.post(
        "/api/pattern/detect-batch",
        files=[
            ("files", ("a.png", b"a", "image/png")),
            ("files", ("b.png", b"b", "image/png")),
        ],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["shot_count"] == 3
    assert body["recoil_step_count"] == 2
    assert body["sample_count"] == 5
    assert body["skipped_sample_count"] == 1
    assert body["detection_mode"] == "target"


def test_recalculate_pattern_marks_manual_mode():
    response = client.post(
        "/api/pattern/recalculate",
        json={
            "points": [{"x": 100, "y": 300}, {"x": 97, "y": 255}],
            "scale_x": 1,
            "scale_y": 1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["shot_count"] == 2
    assert body["recoil_step_count"] == 1
    assert body["detection_mode"] == "manual"
    assert body["pattern"] == [{"y": 45.0, "x": 3.0}]
