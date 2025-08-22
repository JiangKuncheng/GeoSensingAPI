"""
地面传感器从零布设模块 - GeoJSON版本

该模块用于从零开始设计地面观测站网络，支持GeoJSON格式的输入输出。

主要功能：
1. GeoJSON格式的目标区域输入
2. 基于MCLP算法的传感器选址
3. GeoJSON格式的结果输出
4. 完整的覆盖分析和可视化

作者：GeoSensingAPI
"""

import numpy as np
import json
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, mapping, shape
from typing import List, Tuple, Dict, Any
import random
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class GeoJSONGroundSensorFromScratchSolver:
    """
    地面传感器从零布设求解器 - GeoJSON版本
    
    使用GeoJSON格式处理输入输出，基于MCLP算法进行传感器选址优化
    """
    
    def __init__(self, target_area_geojson: Dict[str, Any], 
                 coverage_ratio: float, sensor_radius: float,
                 grid_resolution: float = 0.5):
        """
        初始化求解器
        
        参数:
            target_area_geojson: GeoJSON格式的目标区域
            coverage_ratio: 目标覆盖率 (0-1)
            sensor_radius: 传感器观测半径
            grid_resolution: 网格分辨率
        """
        self.target_area_geojson = target_area_geojson
        self.coverage_ratio = coverage_ratio
        self.sensor_radius = sensor_radius
        self.grid_resolution = grid_resolution
        
        # 解析GeoJSON创建目标区域
        self.target_area = shape(target_area_geojson['geometry'])
        
        # 初始化网格点和传感器
        self.grid_points = []
        self.selected_stations = []
        self._initialize_grid()
        
    def _initialize_grid(self):
        """初始化目标区域的网格点"""
        minx, miny, maxx, maxy = self.target_area.bounds
        x_coords = np.arange(minx, maxx + self.grid_resolution, self.grid_resolution)
        y_coords = np.arange(miny, maxy + self.grid_resolution, self.grid_resolution)
        
        self.grid_points = []
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point) or self.target_area.touches(point):
                    self.grid_points.append((x, y))
        
        print(f"网格点总数: {len(self.grid_points)}")
    
    def _calculate_coverage_for_position(self, station_pos: Tuple[float, float]) -> set:
        """计算指定位置传感器能覆盖的网格点"""
        covered_points = set()
        station_point = Point(station_pos)
        
        for i, (x, y) in enumerate(self.grid_points):
            point = Point(x, y)
            if station_point.distance(point) <= self.sensor_radius:
                covered_points.add(i)
        
        return covered_points
    
    def _get_candidate_positions(self) -> List[Tuple[float, float]]:
        """获取候选传感器位置"""
        minx, miny, maxx, maxy = self.target_area.bounds
        
        # 生成候选位置（在目标区域内）
        candidates = []
        step = self.sensor_radius / 2  # 候选位置的间隔
        
        x_coords = np.arange(minx, maxx + step, step)
        y_coords = np.arange(miny, maxy + step, step)
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point):
                    candidates.append((x, y))
        
        print(f"候选位置数量: {len(candidates)}")
        return candidates
    
    def solve(self) -> Tuple[Dict[str, Any], int, float]:
        """
        求解传感器布设问题
        
        返回:
            stations_geojson: GeoJSON格式的传感器位置
            num_stations: 传感器数量
            actual_coverage: 实际覆盖率
        """
        print("开始求解地面传感器布设问题...")
        
        target_covered_points = int(len(self.grid_points) * self.coverage_ratio)
        covered_points = set()
        self.selected_stations = []
        
        # 获取候选位置
        candidate_positions = self._get_candidate_positions()
        
        # 贪心算法选择传感器位置
        while len(covered_points) < target_covered_points and candidate_positions:
            best_position = None
            best_new_coverage = 0
            
            # 寻找能覆盖最多新点的位置
            for pos in candidate_positions:
                coverage = self._calculate_coverage_for_position(pos)
                new_coverage = len(coverage - covered_points)
                
                if new_coverage > best_new_coverage:
                    best_new_coverage = new_coverage
                    best_position = pos
            
            if best_position is None or best_new_coverage == 0:
                break
            
            # 添加最佳位置
            self.selected_stations.append(best_position)
            covered_points.update(self._calculate_coverage_for_position(best_position))
            
            # 移除附近的候选位置（避免传感器过于密集）
            min_distance = self.sensor_radius * 0.8
            candidate_positions = [
                pos for pos in candidate_positions 
                if Point(pos).distance(Point(best_position)) > min_distance
            ]
            
            print(f"选择传感器 {len(self.selected_stations)}: 位置 {best_position}, "
                  f"累计覆盖率: {len(covered_points)/len(self.grid_points)*100:.1f}%")
        
        actual_coverage = len(covered_points) / len(self.grid_points)
        
        # 转换为GeoJSON格式
        stations_geojson = self._convert_stations_to_geojson()
        
        print(f"\n求解完成:")
        print(f"- 所需传感器数量: {len(self.selected_stations)}")
        print(f"- 实际覆盖率: {actual_coverage*100:.2f}%")
        print(f"- 目标覆盖率: {self.coverage_ratio*100:.2f}%")
        
        return stations_geojson, len(self.selected_stations), actual_coverage
    
    def _convert_stations_to_geojson(self) -> Dict[str, Any]:
        """将传感器位置转换为GeoJSON格式"""
        features = []
        
        for i, (x, y) in enumerate(self.selected_stations):
            # 创建传感器点要素
            point_feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y]
                },
                "properties": {
                    "id": i,
                    "sensor_type": "ground_sensor",
                    "radius": self.sensor_radius,
                    "coverage_area": np.pi * self.sensor_radius ** 2
                }
            }
            features.append(point_feature)
            
            # 创建传感器覆盖区域要素
            coverage_circle = Point(x, y).buffer(self.sensor_radius)
            coverage_feature = {
                "type": "Feature", 
                "geometry": mapping(coverage_circle),
                "properties": {
                    "id": i,
                    "type": "coverage_area",
                    "sensor_id": i,
                    "radius": self.sensor_radius
                }
            }
            features.append(coverage_feature)
        
        geojson_result = {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "algorithm": "ground_sensor_from_scratch",
                "total_sensors": len(self.selected_stations),
                "sensor_radius": self.sensor_radius,
                "target_coverage_ratio": self.coverage_ratio,
                "actual_coverage_ratio": self._calculate_actual_coverage(),
                "target_area": self.target_area_geojson
            }
        }
        
        return geojson_result
    
    def _calculate_actual_coverage(self) -> float:
        """计算实际覆盖率"""
        if not self.selected_stations:
            return 0.0
        
        covered_points = set()
        for station in self.selected_stations:
            covered_points.update(self._calculate_coverage_for_position(station))
        
        return len(covered_points) / len(self.grid_points)
    
    def export_results_geojson(self, filename: str):
        """导出GeoJSON格式结果"""
        stations_geojson, num_stations, coverage = self.solve()
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(stations_geojson, f, ensure_ascii=False, indent=2)
        
        print(f"结果已导出到: {filename}")
    
    def visualize_geojson(self, stations_geojson: Dict[str, Any], 
                         title: str = "地面传感器布设结果 (GeoJSON)"):
        """可视化GeoJSON结果"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # 绘制目标区域
        if self.target_area.geom_type == 'Polygon':
            x, y = self.target_area.exterior.xy
            ax.plot(x, y, 'b-', linewidth=2, label='目标区域边界')
            ax.fill(x, y, alpha=0.2, color='lightblue', label='目标区域')
        
        # 绘制传感器和覆盖区域
        sensor_count = 0
        for feature in stations_geojson['features']:
            geom = shape(feature['geometry'])
            props = feature['properties']
            
            if feature['geometry']['type'] == 'Point':
                # 绘制传感器位置
                x, y = geom.x, geom.y
                ax.scatter(x, y, c='red', s=100, marker='o', 
                          edgecolors='black', linewidth=2, zorder=5)
                ax.annotate(f'S{props["id"]}', (x, y), xytext=(5, 5), 
                           textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7))
                sensor_count += 1
                
            elif props.get('type') == 'coverage_area':
                # 绘制覆盖区域
                if geom.geom_type == 'Polygon':
                    x_coords, y_coords = geom.exterior.xy
                    ax.fill(x_coords, y_coords, alpha=0.3, color='green')
                    ax.plot(x_coords, y_coords, color='green', linewidth=1)
        
        # 设置图形属性
        ax.set_xlabel('X 坐标 (km)', fontsize=12)
        ax.set_ylabel('Y 坐标 (km)', fontsize=12)
        
        # 从GeoJSON中获取统计信息
        props = stations_geojson.get('properties', {})
        actual_coverage = props.get('actual_coverage_ratio', 0) * 100
        target_coverage = props.get('target_coverage_ratio', 0) * 100
        
        ax.set_title(f'{title}\n'
                    f'传感器数量: {sensor_count//2}, '  # 除以2因为每个传感器有点和覆盖区域两个要素
                    f'覆盖率: {actual_coverage:.1f}% (目标: {target_coverage:.1f}%)', 
                    fontsize=14, fontweight='bold')
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # 调整坐标轴范围
        minx, miny, maxx, maxy = self.target_area.bounds
        margin = 1.0
        ax.set_xlim(minx - margin, maxx + margin)
        ax.set_ylim(miny - margin, maxy + margin)
        
        plt.tight_layout()
        plt.show()

def create_test_geojson() -> Dict[str, Any]:
    """创建测试用的GeoJSON目标区域"""
    # 创建一个矩形区域
    target_area_geojson = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [10, 0], [10, 8], [0, 8], [0, 0]]]
        },
        "properties": {
            "name": "测试监测区域",
            "area_type": "rectangular",
            "description": "10x8公里的矩形监测区域"
        }
    }
    return target_area_geojson

def demo_geojson_ground_sensor_from_scratch():
    """演示GeoJSON格式的地面传感器从零布设"""
    print("="*60)
    print("GeoJSON格式地面传感器从零布设演示")
    print("="*60)
    
    # 创建测试输入
    target_area_geojson = create_test_geojson()
    coverage_ratio = 0.85
    sensor_radius = 2.5
    grid_resolution = 0.5
    
    print("输入参数:")
    print(f"- 目标区域: {target_area_geojson['properties']['description']}")
    print(f"- 目标覆盖率: {coverage_ratio*100}%")
    print(f"- 传感器半径: {sensor_radius} km")
    print(f"- 网格分辨率: {grid_resolution} km")
    
    # 创建求解器
    solver = GeoJSONGroundSensorFromScratchSolver(
        target_area_geojson=target_area_geojson,
        coverage_ratio=coverage_ratio,
        sensor_radius=sensor_radius,
        grid_resolution=grid_resolution
    )
    
    # 求解
    stations_geojson, num_stations, actual_coverage = solver.solve()
    
    # 输出结果
    print(f"\n=== GeoJSON输出结果 ===")
    print(f"传感器数量: {num_stations}")
    print(f"实际覆盖率: {actual_coverage*100:.2f}%")
    print(f"GeoJSON要素数量: {len(stations_geojson['features'])}")
    
    # 导出GeoJSON文件
    output_filename = "ground_sensor_result.geojson"
    solver.export_results_geojson(output_filename)
    
    # 可视化结果（在测试环境中跳过）
    try:
        solver.visualize_geojson(stations_geojson)
    except:
        print("跳过可视化（可能在无图形界面环境中运行）")
    
    # 显示部分GeoJSON内容
    print(f"\n=== GeoJSON示例内容 ===")
    print(json.dumps(stations_geojson['features'][0], indent=2, ensure_ascii=False))
    
    return solver, stations_geojson

if __name__ == "__main__":
    demo_geojson_ground_sensor_from_scratch()
