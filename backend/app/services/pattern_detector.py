"""
弹道图识别服务
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Literal, Sequence

import cv2
import numpy as np

from ..models.schemas import Point, RecoilData

DetectionMode = Literal["auto", "green", "target"]
ResolvedDetectionMode = Literal["green", "target", "manual"]


@dataclass(frozen=True)
class DetectionResult:
    points: List[Point]
    width: int
    height: int
    detection_mode: ResolvedDetectionMode


@dataclass(frozen=True)
class AggregateDetectionResult:
    points: List[Point]
    width: int
    height: int
    detection_mode: ResolvedDetectionMode
    sample_count: int
    skipped_sample_count: int


class PatternDetector:
    """弹道图识别器"""

    def __init__(self, min_dist: int = 5):
        self.min_dist = max(1, min_dist)

    def detect_from_bytes(
        self,
        image_bytes: bytes,
        detection_mode: DetectionMode = "auto",
    ) -> DetectionResult:
        """
        从图片字节中识别弹孔/绿点。
        """
        image = self._decode_image(image_bytes)
        height, width = image.shape[:2]
        points, resolved_mode = self._detect_points(image, detection_mode)
        return DetectionResult(points=points, width=width, height=height, detection_mode=resolved_mode)

    def detect_from_multiple_bytes(
        self,
        images: Sequence[bytes],
        detection_mode: DetectionMode = "auto",
    ) -> AggregateDetectionResult:
        """
        从多张靶场图中识别并聚合出更稳健的弹道。
        """
        decoded_images = [self._decode_image(image_bytes) for image_bytes in images]
        if not decoded_images:
            raise ValueError("至少需要一张图片")

        detections: list[DetectionResult] = []
        for image in decoded_images:
            height, width = image.shape[:2]
            points, resolved_mode = self._detect_points(image, detection_mode)
            if points:
                detections.append(
                    DetectionResult(
                        points=points,
                        width=width,
                        height=height,
                        detection_mode=resolved_mode,
                    )
                )

        if not detections:
            raise ValueError("未能从上传样本中识别到有效弹孔")

        shot_count = self._determine_target_shot_count(len(result.points) for result in detections)
        normalized_detections = [
            DetectionResult(
                points=self._trim_points_to_count(result.points, shot_count),
                width=result.width,
                height=result.height,
                detection_mode=result.detection_mode,
            )
            for result in detections
        ]

        grouped_points = self._cluster_shots_by_index(normalized_detections, shot_count)
        aggregated_points = [self._average_points(group) for group in grouped_points if group]

        if len(aggregated_points) < 2:
            raise ValueError("有效弹孔不足，无法计算聚合弹道")

        reference = max(normalized_detections, key=lambda result: (len(result.points), result.width * result.height))
        skipped = len(decoded_images) - len(detections)
        resolved_mode = "target" if any(item.detection_mode == "target" for item in normalized_detections) else "green"

        return AggregateDetectionResult(
            points=aggregated_points,
            width=reference.width,
            height=reference.height,
            detection_mode=resolved_mode,
            sample_count=len(detections),
            skipped_sample_count=skipped,
        )

    def _decode_image(self, image_bytes: bytes) -> np.ndarray:
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解析图片数据")
        return image

    def _detect_points(
        self,
        image: np.ndarray,
        detection_mode: DetectionMode,
    ) -> tuple[List[Point], ResolvedDetectionMode]:
        if detection_mode == "green":
            return self._find_green_points(image), "green"
        if detection_mode == "target":
            return self._find_target_holes(image), "target"

        green_points = self._find_green_points(image)
        if len(green_points) >= 2:
            return green_points, "green"

        target_points = self._find_target_holes(image)
        if target_points:
            return target_points, "target"

        return green_points, "green"

    def _find_green_points(self, image: np.ndarray) -> List[Point]:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_green = np.array([30, 30, 30])
        upper_green = np.array([95, 255, 255])
        mask = cv2.inRange(hsv, lower_green, upper_green)

        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        kernel = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(dist_transform, kernel)
        local_max = (dist_transform == dilated) & (dist_transform > 2)
        coords = np.column_stack(np.where(local_max))
        coord_values = [(y, x, dist_transform[y, x]) for y, x in coords]
        coord_values.sort(key=lambda coord: -coord[2])

        points = self._dedupe_subpixel_points(dist_transform, coord_values)
        return self._sort_points(points)

    def _find_target_holes(self, image: np.ndarray) -> List[Point]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        crop, origin_x, origin_y = self._crop_target_region(gray)
        if crop.size == 0:
            return []

        blackhat = self._build_blackhat(crop)
        candidate_masks = [
            self._threshold_mask(blackhat, percentile)
            for percentile in (99.4, 99.1, 98.8, 98.4, 98.0)
        ]

        candidates: list[tuple[float, float, float]] = []
        for mask in candidate_masks:
            candidates.extend(self._extract_hole_candidates(mask, crop, origin_x, origin_y))

        merged_candidates = self._merge_hole_candidates(candidates)
        points = self._clean_target_points(merged_candidates, image.shape[1])
        return self._sort_points(points)

    def _crop_target_region(self, gray: np.ndarray) -> tuple[np.ndarray, int, int]:
        height, width = gray.shape[:2]
        margin_x = max(10, int(width * 0.12))
        margin_y = max(6, int(height * 0.02))
        return gray[margin_y : height - margin_y, margin_x : width - margin_x], margin_x, margin_y

    def _build_blackhat(self, crop: np.ndarray) -> np.ndarray:
        blur = cv2.GaussianBlur(crop, (5, 5), 0)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))
        return cv2.morphologyEx(blur, cv2.MORPH_BLACKHAT, kernel)

    def _threshold_mask(self, blackhat: np.ndarray, percentile: float) -> np.ndarray:
        threshold = max(16, int(np.percentile(blackhat, percentile)))
        _, mask = cv2.threshold(blackhat, threshold, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return cv2.dilate(mask, kernel, iterations=1)

    def _extract_hole_candidates(
        self,
        mask: np.ndarray,
        crop: np.ndarray,
        origin_x: int,
        origin_y: int,
    ) -> list[tuple[float, float, float]]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates: list[tuple[float, float, float]] = []

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 8 or area > 260:
                continue

            perimeter = cv2.arcLength(contour, True)
            circularity = 0.0 if perimeter == 0 else 4 * math.pi * area / (perimeter * perimeter)
            if circularity < 0.12:
                continue

            (center_x, center_y), radius = cv2.minEnclosingCircle(contour)
            if radius < 2 or radius > 15:
                continue

            patch_radius = max(2, int(round(radius * 1.5)))
            y1 = max(0, int(center_y) - patch_radius)
            y2 = min(crop.shape[0], int(center_y) + patch_radius + 1)
            x1 = max(0, int(center_x) - patch_radius)
            x2 = min(crop.shape[1], int(center_x) + patch_radius + 1)
            patch = crop[y1:y2, x1:x2]
            if patch.size == 0:
                continue

            darkness = 255.0 - float(np.mean(patch))
            score = area * max(circularity, 0.2) + darkness * 0.2
            candidates.append((center_x + origin_x, center_y + origin_y, score))

        return candidates

    def _merge_hole_candidates(self, candidates: Iterable[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
        sorted_candidates = sorted(candidates, key=lambda item: (-item[2], item[1]))
        merged: list[tuple[float, float, float]] = []
        merge_radius = max(6.0, float(self.min_dist) * 1.6)

        for center_x, center_y, _score in sorted_candidates:
            if any(
                math.hypot(point_x - center_x, point_y - center_y) < merge_radius
                for point_x, point_y, _point_score in merged
            ):
                continue
            merged.append((center_x, center_y, _score))

        return merged

    def _clean_target_points(
        self,
        candidates: Sequence[tuple[float, float, float]],
        image_width: int,
    ) -> List[Point]:
        if not candidates:
            return []

        median_x = float(np.median([candidate[0] for candidate in candidates]))
        horizontal_limit = max(18.0, image_width * 0.12)
        filtered = [candidate for candidate in candidates if abs(candidate[0] - median_x) <= horizontal_limit]
        if len(filtered) < 2:
            filtered = list(candidates)

        filtered.sort(key=lambda item: -item[1])
        filtered = self._remove_too_close_points(filtered)

        return [Point(x=point_x, y=point_y) for point_x, point_y, _score in filtered]

    def _remove_too_close_points(
        self,
        points: Sequence[tuple[float, float, float]],
    ) -> list[tuple[float, float, float]]:
        cleaned = list(points)
        while len(cleaned) >= 3:
            gaps = [cleaned[index][1] - cleaned[index + 1][1] for index in range(len(cleaned) - 1)]
            typical_gap = float(np.median(gaps)) if gaps else 0.0
            min_gap = max(float(self.min_dist) * 2.5, typical_gap * 0.55)
            smallest_gap = min(gaps, default=float("inf"))
            if smallest_gap >= min_gap:
                break

            gap_index = gaps.index(smallest_gap)
            lower = cleaned[gap_index]
            upper = cleaned[gap_index + 1]
            remove_index = gap_index + 1
            if lower[2] < upper[2]:
                remove_index = gap_index
            cleaned.pop(remove_index)

        return cleaned

    def _determine_target_shot_count(self, counts: Iterable[int]) -> int:
        count_list = [count for count in counts if count >= 2]
        if not count_list:
            raise ValueError("有效弹孔不足，无法聚合")

        frequency = Counter(count_list)
        most_common = frequency.most_common()
        highest_frequency = most_common[0][1]
        candidates = [count for count, times in most_common if times == highest_frequency]
        if len(candidates) == 1:
            return candidates[0]

        return int(round(float(np.median(candidates))))

    def _trim_points_to_count(self, points: Sequence[Point], target_count: int) -> List[Point]:
        trimmed = list(points)
        while len(trimmed) > target_count:
            median_x = float(np.median([point.x for point in trimmed]))
            gaps = [trimmed[index].y - trimmed[index + 1].y for index in range(len(trimmed) - 1)]
            typical_gap = float(np.median(gaps)) if gaps else 0.0

            best_index = len(trimmed) - 1
            best_priority = float("inf")
            for index, point in enumerate(trimmed):
                prev_gap = gaps[index - 1] if index > 0 else float("inf")
                next_gap = gaps[index] if index < len(gaps) else float("inf")
                close_gap = min(prev_gap, next_gap)
                x_deviation = abs(point.x - median_x)
                top_edge_bonus = 12.0 if point.y < 20 else 0.0
                priority = close_gap - (x_deviation * 0.35) - top_edge_bonus

                if priority < best_priority or (
                    math.isclose(priority, best_priority) and index > best_index
                ):
                    best_priority = priority
                    best_index = index

            if typical_gap > 0:
                smallest_gap = min(gaps, default=typical_gap)
                min_reasonable_gap = max(float(self.min_dist) * 2.5, typical_gap * 0.55)
                if smallest_gap >= min_reasonable_gap and best_index == len(trimmed) - 1:
                    best_index = len(trimmed) - 1

            trimmed.pop(best_index)

        return trimmed

    def _dedupe_subpixel_points(
        self,
        dist_transform: np.ndarray,
        coord_values: Iterable[tuple[int, int, float]],
    ) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        window = 3

        for y, x, _value in coord_values:
            if any(abs(prev_y - y) < self.min_dist and abs(prev_x - x) < self.min_dist for prev_y, prev_x in points):
                continue

            y1 = max(0, y - window)
            y2 = min(dist_transform.shape[0], y + window + 1)
            x1 = max(0, x - window)
            x2 = min(dist_transform.shape[1], x + window + 1)
            region = dist_transform[y1:y2, x1:x2]
            total_weight = float(np.sum(region))

            if total_weight > 0:
                yy, xx = np.mgrid[y1:y2, x1:x2]
                sub_y = float(np.sum(yy * region) / total_weight)
                sub_x = float(np.sum(xx * region) / total_weight)
                points.append((sub_y, sub_x))
            else:
                points.append((float(y), float(x)))

        return points

    def _sort_points(self, points: Iterable[Point] | Iterable[tuple[float, float]]) -> List[Point]:
        normalized: list[Point] = []
        for item in points:
            if isinstance(item, Point):
                normalized.append(item)
            else:
                first, second = item
                normalized.append(Point(x=float(second), y=float(first)))

        normalized.sort(key=lambda point: -point.y)
        return normalized

    def _cluster_shots_by_index(
        self,
        detections: Sequence[DetectionResult],
        shot_count: int,
    ) -> list[list[Point]]:
        groups = [[] for _ in range(shot_count)]
        for detection in detections:
            for index, point in enumerate(detection.points):
                groups[index].append(point)
        return groups

    def _average_points(self, points: Sequence[Point]) -> Point:
        average_x = sum(point.x for point in points) / len(points)
        average_y = sum(point.y for point in points) / len(points)
        return Point(x=round(average_x, 6), y=round(average_y, 6))

    @staticmethod
    def calculate_recoil_pattern(
        points: List[Point],
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ) -> List[RecoilData]:
        """
        计算相邻弹孔之间的补偿数据。
        N 个弹孔只会生成 N-1 段补偿。
        """
        if len(points) < 2:
            return []

        pattern = []
        for index in range(1, len(points)):
            previous = points[index - 1]
            current = points[index]
            delta_y = (previous.y - current.y) * scale_y
            delta_x = (previous.x - current.x) * scale_x
            pattern.append(RecoilData(y=round(delta_y, 6), x=round(delta_x, 6)))

        return pattern
