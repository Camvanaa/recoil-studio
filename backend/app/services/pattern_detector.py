"""
弹道图识别服务
"""
import cv2
import numpy as np
from typing import List, Tuple
from ..models.schemas import Point, RecoilData


class PatternDetector:
    """弹道图识别器"""
    
    def __init__(self, min_dist: int = 5):
        self.min_dist = min_dist
    
    def detect_from_bytes(self, image_bytes: bytes) -> Tuple[List[Point], int, int]:
        """
        从图片字节数据中识别弹道点
        返回: (点列表, 图片宽度, 图片高度)
        """
        # 将字节转换为numpy数组
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("无法解析图片数据")
        
        height, width = img.shape[:2]
        points = self._find_bullet_points(img)
        
        return points, width, height
    
    def _find_bullet_points(self, img: np.ndarray) -> List[Point]:
        """识别图片中的绿色弹道点"""
        # 转换到HSV颜色空间
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 绿色范围
        lower_green = np.array([30, 30, 30])
        upper_green = np.array([95, 255, 255])
        
        # 创建掩码
        mask = cv2.inRange(hsv, lower_green, upper_green)
        
        # 距离变换
        dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
        
        # 膨胀找局部最大值
        kernel_size = 5
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        dilated = cv2.dilate(dist_transform, kernel)
        
        # 局部最大值
        local_max = (dist_transform == dilated) & (dist_transform > 2)
        coords = np.column_stack(np.where(local_max))
        
        # 按距离变换值排序
        coord_values = [(y, x, dist_transform[y, x]) for y, x in coords]
        coord_values.sort(key=lambda c: -c[2])
        
        # 亚像素精度计算
        points = []
        window = 3
        
        for y, x, val in coord_values:
            # 检查是否与已有点太近
            too_close = False
            for py, px in points:
                if abs(py - y) < self.min_dist and abs(px - x) < self.min_dist:
                    too_close = True
                    break
            
            if not too_close:
                # 计算亚像素质心
                y1 = max(0, y - window)
                y2 = min(dist_transform.shape[0], y + window + 1)
                x1 = max(0, x - window)
                x2 = min(dist_transform.shape[1], x + window + 1)
                
                region = dist_transform[y1:y2, x1:x2]
                total_weight = np.sum(region)
                
                if total_weight > 0:
                    yy, xx = np.mgrid[y1:y2, x1:x2]
                    sub_y = float(np.sum(yy * region) / total_weight)
                    sub_x = float(np.sum(xx * region) / total_weight)
                    points.append((sub_y, sub_x))
                else:
                    points.append((float(y), float(x)))
        
        # 转换为 (x, y) 格式并按Y从下到上排序
        result = [Point(x=x, y=y) for y, x in points]
        result.sort(key=lambda p: -p.y)  # 从下到上
        
        return result
    
    @staticmethod
    def calculate_recoil_pattern(
        points: List[Point], 
        scale_x: float = 1.0, 
        scale_y: float = 1.0
    ) -> List[RecoilData]:
        """
        计算相邻点之间的后坐力数据
        """
        if len(points) < 2:
            return []
        
        pattern = []
        
        for i in range(1, len(points)):
            prev = points[i - 1]
            curr = points[i]
            
            # 弹道从下往上，后坐力 = prev.y - curr.y
            delta_y = (prev.y - curr.y) * scale_y
            delta_x = (prev.x - curr.x) * scale_x
            
            pattern.append(RecoilData(
                y=round(delta_y, 6),
                x=round(delta_x, 6)
            ))
        
        return pattern
