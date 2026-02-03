"""
弹道图识别工具 - 从弹道图片自动生成Lua配置
使用方法: python pattern_generator.py <图片路径> [枪械名称] [RPM射速]

示例: python pattern_generator.py TEST.png AK-47 600
"""

import cv2
import numpy as np
import sys
import os

def find_bullet_points(image_path, debug=False):
    """
    识别图片中的绿色弹道点
    弹道图是从下往上的（第1发在底部，最后1发在顶部）
    返回按Y坐标排序的点列表 (从下到上，即第1发到最后1发)
    """
    # 读取图片
    img = cv2.imread(image_path)
    if img is None:
        print(f"错误: 无法读取图片 {image_path}")
        return None
    
    # 转换到HSV颜色空间
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 扩大绿色范围，捕捉变淡的点
    lower_green = np.array([30, 30, 30])
    upper_green = np.array([95, 255, 255])
    
    # 创建绿色掩码
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # 保存mask用于调试
    if debug:
        cv2.imwrite(image_path.replace('.png', '_mask.png'), mask)
    
    # 使用距离变换 + 分水岭算法分离重叠的圆
    # 距离变换
    dist_transform = cv2.distanceTransform(mask, cv2.DIST_L2, 5)
    
    # 归一化距离变换用于调试
    if debug:
        dist_normalized = cv2.normalize(dist_transform, None, 0, 255, cv2.NORM_MINMAX)
        cv2.imwrite(image_path.replace('.png', '_dist.png'), dist_normalized)
    
    # 找到局部最大值作为圆心
    # 使用膨胀找局部最大值
    kernel_size = 5
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    dilated = cv2.dilate(dist_transform, kernel)
    
    # 局部最大值：膨胀后的值等于原始值的点
    local_max = (dist_transform == dilated) & (dist_transform > 2)
    
    # 获取局部最大值的坐标
    coords = np.column_stack(np.where(local_max))
    
    # 过滤太近的点（保留距离变换值更大的）
    points = []
    min_dist = 5  # 两点之间最小距离
    
    # 按距离变换值排序（从大到小），优先保留中心更明显的点
    coord_values = [(y, x, dist_transform[y, x]) for y, x in coords]
    coord_values.sort(key=lambda c: -c[2])
    
    # 用于计算亚像素精度的窗口大小
    window = 3
    
    for y, x, val in coord_values:
        # 检查是否与已有点太近
        too_close = False
        for py, px in points:
            if abs(py - y) < min_dist and abs(px - x) < min_dist:
                too_close = True
                break
        if not too_close:
            # 计算亚像素精度的质心
            y1 = max(0, y - window)
            y2 = min(dist_transform.shape[0], y + window + 1)
            x1 = max(0, x - window)
            x2 = min(dist_transform.shape[1], x + window + 1)
            
            region = dist_transform[y1:y2, x1:x2]
            total_weight = np.sum(region)
            
            if total_weight > 0:
                # 加权质心计算亚像素位置
                yy, xx = np.mgrid[y1:y2, x1:x2]
                sub_y = np.sum(yy * region) / total_weight
                sub_x = np.sum(xx * region) / total_weight
                points.append((sub_y, sub_x))
            else:
                points.append((float(y), float(x)))
    
    # 转换为 (x, y) 格式
    points = [(x, y) for y, x in points]
    
    print(f"距离变换检测到 {len(points)} 个点")
    
    # 如果点数还不够，降低阈值再试
    if len(points) < 20:
        print("尝试降低阈值检测更多点...")
        local_max2 = (dist_transform == dilated) & (dist_transform > 1)
        coords2 = np.column_stack(np.where(local_max2))
        
        coord_values2 = [(y, x, dist_transform[y, x]) for y, x in coords2]
        coord_values2.sort(key=lambda c: -c[2])
        
        for y, x, val in coord_values2:
            too_close = False
            for px, py in points:
                if abs(py - y) < min_dist and abs(px - x) < min_dist:
                    too_close = True
                    break
            if not too_close:
                # 计算亚像素精度的质心
                y1 = max(0, y - window)
                y2 = min(dist_transform.shape[0], y + window + 1)
                x1 = max(0, x - window)
                x2 = min(dist_transform.shape[1], x + window + 1)
                
                region = dist_transform[y1:y2, x1:x2]
                total_weight = np.sum(region)
                
                if total_weight > 0:
                    yy, xx = np.mgrid[y1:y2, x1:x2]
                    sub_y = np.sum(yy * region) / total_weight
                    sub_x = np.sum(xx * region) / total_weight
                    points.append((sub_x, sub_y))
                else:
                    points.append((float(x), float(y)))
        
        print(f"补充后共 {len(points)} 个点")
    
    # 按Y坐标排序：从下到上（Y值从大到小）= 第1发到最后1发
    points.sort(key=lambda p: -p[1])
    
    # Debug: 保存标记后的图片
    if debug:
        debug_img = img.copy()
        for i, (x, y) in enumerate(points):
            # 转换为整数用于绘图
            ix, iy = int(round(x)), int(round(y))
            cv2.circle(debug_img, (ix, iy), 4, (0, 0, 255), -1)
            cv2.putText(debug_img, str(i+1), (ix+8, iy+4), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        debug_path = image_path.replace('.png', '_debug.png').replace('.jpg', '_debug.jpg')
        cv2.imwrite(debug_path, debug_img)
        print(f"Debug图片已保存: {debug_path}")
    
    return points


def calculate_recoil_pattern(points, scale_x=1.0, scale_y=1.0):
    """
    计算相邻点之间的偏移量，生成后坐力配置
    
    弹道图显示的是子弹落点（从下往上）：
    - 子弹往上飘（y减小），我们需要向下压（y为正）
    - 子弹往右偏（x增大），我们需要向左补（x为负）
    """
    if len(points) < 2:
        print("错误: 至少需要2个弹道点")
        return None
    
    pattern = []
    
    for i in range(1, len(points)):
        prev_x, prev_y = points[i-1]
        curr_x, curr_y = points[i]
        
        # 弹道从下往上，所以curr_y < prev_y（Y坐标减小）
        # 后坐力 = 子弹往上飘了多少 = prev_y - curr_y（正值）
        # 我们需要向下压枪来补偿
        delta_y = (prev_y - curr_y) * scale_y
        
        # X方向：子弹往左偏时 curr_x < prev_x
        # 我们需要向左补偿（负值），所以直接用 prev_x - curr_x
        delta_x = (prev_x - curr_x) * scale_x
        
        pattern.append({
            'y': delta_y,
            'x': delta_x
        })
    
    return pattern


def generate_lua_config(pattern, gun_name="CustomGun", rpm=600, 
                        vertical_mul=1.0, horizontal_mul=1.0):
    """
    生成Lua配置代码
    """
    lines = []
    lines.append(f"    -- {gun_name}")
    lines.append("    {")
    lines.append(f'        name = "{gun_name}",')
    lines.append(f'        rpm = {rpm},')
    lines.append(f'        verticalMul = {vertical_mul},')
    lines.append(f'        horizontalMul = {horizontal_mul},')
    lines.append('        pattern = {')
    
    for i, p in enumerate(pattern):
        # 保留6位小数，去掉浮点误差
        y_val = round(p['y'], 6)
        x_val = round(p['x'], 6)
        comment = f"-- 第{i+1}发"
        lines.append(f'            {{y={y_val}, x={x_val}}},    {comment}')
    
    lines.append('        }')
    lines.append('    },')
    
    return '\n'.join(lines)


def print_usage():
    print("""
弹道图识别工具 - 从弹道图片自动生成Lua配置
============================================

使用方法:
  python pattern_generator.py <图片路径> [选项]

参数:
  图片路径          弹道图片文件 (支持PNG/JPG)

选项:
  --name <名称>     枪械名称 (默认: CustomGun)
  --rpm <数值>      每分钟射速 (默认: 600)
  --scale-x <数值>  X轴缩放倍率 (默认: 1.0)
  --scale-y <数值>  Y轴缩放倍率 (默认: 1.0)
  --vmul <数值>     垂直倍率 (默认: 1.0)
  --hmul <数值>     水平倍率 (默认: 1.0)
  --debug           保存带标记的调试图片
  --help            显示此帮助信息

示例:
  python pattern_generator.py TEST.png --name AK-47 --rpm 600
  python pattern_generator.py gun.png --name M4A1 --rpm 700 --scale-y 0.8
  python pattern_generator.py recoil.png --debug

输出:
  脚本会输出可以直接复制到 macro-G502.lua 的配置代码
""")


def main():
    # 解析命令行参数
    if len(sys.argv) < 2 or '--help' in sys.argv:
        print_usage()
        return
    
    image_path = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(image_path):
        print(f"错误: 文件不存在 - {image_path}")
        return
    
    # 默认参数
    gun_name = "CustomGun"
    rpm = 600
    scale_x = 1.0
    scale_y = 1.0
    vertical_mul = 1.0
    horizontal_mul = 1.0
    debug = '--debug' in sys.argv
    
    # 解析可选参数
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--name' and i+1 < len(args):
            gun_name = args[i+1]
            i += 2
        elif args[i] == '--rpm' and i+1 < len(args):
            rpm = int(args[i+1])
            i += 2
        elif args[i] == '--scale-x' and i+1 < len(args):
            scale_x = float(args[i+1])
            i += 2
        elif args[i] == '--scale-y' and i+1 < len(args):
            scale_y = float(args[i+1])
            i += 2
        elif args[i] == '--vmul' and i+1 < len(args):
            vertical_mul = float(args[i+1])
            i += 2
        elif args[i] == '--hmul' and i+1 < len(args):
            horizontal_mul = float(args[i+1])
            i += 2
        elif args[i] == '--debug':
            i += 1
        else:
            i += 1
    
    print(f"正在分析弹道图: {image_path}")
    print(f"枪械名称: {gun_name}, 射速: {rpm} RPM")
    print("-" * 50)
    
    # 识别弹道点
    points = find_bullet_points(image_path, debug=debug)
    
    if not points:
        print("未能识别到弹道点，请检查图片")
        return
    
    print(f"识别到 {len(points)} 个弹道点")
    
    # 计算后坐力配置
    pattern = calculate_recoil_pattern(points, scale_x, scale_y)
    
    if not pattern:
        return
    
    # 生成Lua配置
    lua_code = generate_lua_config(pattern, gun_name, rpm, vertical_mul, horizontal_mul)
    
    print("\n" + "=" * 50)
    print("生成的Lua配置 (复制到guns表中):")
    print("=" * 50 + "\n")
    print(lua_code)
    print("\n" + "=" * 50)
    
    # 保存到文件
    output_file = image_path.rsplit('.', 1)[0] + '_config.lua'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(lua_code)
    print(f"\n配置已保存到: {output_file}")


if __name__ == "__main__":
    main()
