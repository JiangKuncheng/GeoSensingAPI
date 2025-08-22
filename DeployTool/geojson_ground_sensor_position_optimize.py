"""
地面传感器位置优化模块 - GeoJSON版本

该模块用于优化已有地面传感器的位置布设，支持GeoJSON格式的输入输出。

主要功能：
1. GeoJSON格式的目标区域和现有传感器输入
2. 基于局部搜索的位置优化
3. GeoJSON格式的优化结果输出
4. 优化前后性能对比

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

class GeoJSONGroundSensorPositionOptimizer:
    """
    地面传感器位置优化器 - GeoJSON版本
    
    在不改变传感器数量的情况下，通过调整位置来优化覆盖率
    """
    
    def __init__(self, target_area_geojson: Dict[str, Any], 
                 existing_sensors_geojson: Dict[str, Any],
                 sensor_radius: float, grid_resolution: float = 0.5):
        """
        初始化优化器
        
        参数:
            target_area_geojson: GeoJSON格式的目标区域
            existing_sensors_geojson: GeoJSON格式的现有传感器
            sensor_radius: 传感器观测半径
            grid_resolution: 网格分辨率
        """
        self.target_area_geojson = target_area_geojson
        self.existing_sensors_geojson = existing_sensors_geojson
        self.sensor_radius = sensor_radius
        self.grid_resolution = grid_resolution
        
        # 解析GeoJSON
        self.target_area = shape(target_area_geojson['geometry'])
        self.original_stations = self._parse_sensors_from_geojson(existing_sensors_geojson)
        
        # 初始化网格点
        self.grid_points = []
        self._initialize_grid()
        
    def _parse_sensors_from_geojson(self, sensors_geojson: Dict[str, Any]) -> List[Tuple[float, float]]:
        """从GeoJSON中解析传感器位置"""
        stations = []
        
        if sensors_geojson['type'] == 'FeatureCollection':
            for feature in sensors_geojson['features']:
                if feature['geometry']['type'] == 'Point':
                    coords = feature['geometry']['coordinates']
                    stations.append((coords[0], coords[1]))
        elif sensors_geojson['type'] == 'Feature':
            if sensors_geojson['geometry']['type'] == 'Point':
                coords = sensors_geojson['geometry']['coordinates']
                stations.append((coords[0], coords[1]))
        
        print(f"解析到 {len(stations)} 个现有传感器")
        return stations
    
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
    
    def _evaluate_station_layout(self, stations: List[Tuple[float, float]]) -> float:
        """评估传感器布设方案的覆盖率"""
        covered_points = set()
        
        for station_x, station_y in stations:
            station_point = Point(station_x, station_y)
            for i, (x, y) in enumerate(self.grid_points):
                point = Point(x, y)
                if station_point.distance(point) <= self.sensor_radius:
                    covered_points.add(i)
        
        coverage_ratio = len(covered_points) / len(self.grid_points)
        return coverage_ratio
    
    def _get_candidate_positions(self) -> List[Tuple[float, float]]:
        """获取候选传感器位置"""
        minx, miny, maxx, maxy = self.target_area.bounds
        
        candidates = []
        step = self.sensor_radius / 3  # 候选位置的间隔
        
        x_coords = np.arange(minx, maxx + step, step)
        y_coords = np.arange(miny, maxy + step, step)
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point):
                    candidates.append((x, y))
        
        return candidates
    
    def optimize_positions(self, target_coverage_ratio: float = None,
                         max_iterations: int = 100) -> Tuple[Dict[str, Any], float, Dict]:
        """
        优化传感器位置
        
        参数:
            target_coverage_ratio: 目标覆盖率 (可选)
            max_iterations: 最大迭代次数
            
        返回:
            optimized_geojson: GeoJSON格式的优化结果
            final_coverage: 优化后覆盖率
            optimization_info: 优化过程信息
        """
        print("开始传感器位置优化...")
        
        current_stations = self.original_stations.copy()
        initial_coverage = self._evaluate_station_layout(current_stations)
        
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        
        candidate_positions = self._get_candidate_positions()
        best_coverage = initial_coverage
        best_stations = current_stations.copy()
        iterations_without_improvement = 0
        
        optimization_history = []
        
        for iteration in range(max_iterations):
            improved = False
            
            # 尝试优化每个传感器的位置
            for i in range(len(current_stations)):
                current_pos = current_stations[i]
                best_pos = current_pos
                best_local_coverage = best_coverage
                
                # 在当前位置附近搜索更好的位置
                search_radius = self.sensor_radius * 1.5
                nearby_candidates = [
                    pos for pos in candidate_positions
                    if Point(pos).distance(Point(current_pos)) <= search_radius
                ]
                
                for candidate_pos in nearby_candidates:
                    # 临时更换位置并评估
                    test_stations = current_stations.copy()
                    test_stations[i] = candidate_pos
                    
                    test_coverage = self._evaluate_station_layout(test_stations)
                    
                    if test_coverage > best_local_coverage:
                        best_local_coverage = test_coverage
                        best_pos = candidate_pos
                        improved = True
                
                # 更新最佳位置
                if best_pos != current_pos:
                    current_stations[i] = best_pos
                    best_coverage = best_local_coverage
                    best_stations = current_stations.copy()
            
            # 记录优化历史
            optimization_history.append({
                'iteration': iteration,
                'coverage': best_coverage,
                'improvement': best_coverage - initial_coverage
            })
            
            if improved:
                iterations_without_improvement = 0
                print(f"迭代 {iteration}: 覆盖率 = {best_coverage*100:.2f}%")
            else:
                iterations_without_improvement += 1
            
            # 早停条件
            if target_coverage_ratio and best_coverage >= target_coverage_ratio:
                print(f"达到目标覆盖率，在第 {iteration} 代停止优化")
                break
            
            if iterations_without_improvement >= 10:
                print(f"连续10代无改进，在第 {iteration} 代停止优化")
                break
        
        final_coverage = best_coverage
        improvement = final_coverage - initial_coverage
        
        print(f"\n优化完成:")
        print(f"- 初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"- 最终覆盖率: {final_coverage*100:.2f}%")
        print(f"- 改进幅度: {improvement*100:.2f}个百分点")
        
        # 转换为GeoJSON格式
        optimized_geojson = self._convert_optimization_result_to_geojson(
            self.original_stations, best_stations, initial_coverage, final_coverage
        )
        
        optimization_info = {
            'initial_coverage': initial_coverage,
            'final_coverage': final_coverage,
            'improvement': improvement,
            'iterations': len(optimization_history),
            'history': optimization_history
        }
        
        return optimized_geojson, final_coverage, optimization_info
    
    def _convert_optimization_result_to_geojson(self, original_stations: List[Tuple[float, float]],
                                              optimized_stations: List[Tuple[float, float]],
                                              initial_coverage: float,
                                              final_coverage: float) -> Dict[str, Any]:
        """将优化结果转换为GeoJSON格式"""
        features = []
        
        # 添加原始传感器位置
        for i, (x, y) in enumerate(original_stations):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y]
                },
                "properties": {
                    "id": i,
                    "sensor_type": "original_sensor",
                    "radius": self.sensor_radius,
                    "status": "original"
                }
            }
            features.append(feature)
        
        # 添加优化后传感器位置
        for i, (x, y) in enumerate(optimized_stations):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point", 
                    "coordinates": [x, y]
                },
                "properties": {
                    "id": i,
                    "sensor_type": "optimized_sensor",
                    "radius": self.sensor_radius,
                    "status": "optimized"
                }
            }
            features.append(feature)
            
            # 添加优化后的覆盖区域
            coverage_circle = Point(x, y).buffer(self.sensor_radius)
            coverage_feature = {
                "type": "Feature",
                "geometry": mapping(coverage_circle),
                "properties": {
                    "id": i,
                    "type": "optimized_coverage",
                    "sensor_id": i,
                    "radius": self.sensor_radius
                }
            }
            features.append(coverage_feature)
        
        geojson_result = {
            "type": "FeatureCollection",
            "features": features,
            "properties": {
                "algorithm": "ground_sensor_position_optimize",
                "total_sensors": len(optimized_stations),
                "sensor_radius": self.sensor_radius,
                "initial_coverage_ratio": initial_coverage,
                "final_coverage_ratio": final_coverage,
                "improvement": final_coverage - initial_coverage,
                "target_area": self.target_area_geojson,
                "original_sensors": self.existing_sensors_geojson
            }
        }
        
        return geojson_result
    
    def export_results_geojson(self, filename: str, optimization_result: Dict[str, Any]):
        """导出GeoJSON格式结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(optimization_result, f, ensure_ascii=False, indent=2)
        
        print(f"优化结果已导出到: {filename}")
    
    def visualize_optimization_geojson(self, optimization_geojson: Dict[str, Any],
                                     title: str = "地面传感器位置优化结果 (GeoJSON)"):
        """可视化GeoJSON优化结果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 解析原始和优化后的传感器
        original_sensors = []
        optimized_sensors = []
        coverage_areas = []
        
        for feature in optimization_geojson['features']:
            props = feature['properties']
            geom = shape(feature['geometry'])
            
            if props.get('status') == 'original':
                original_sensors.append((geom.x, geom.y))
            elif props.get('status') == 'optimized':
                optimized_sensors.append((geom.x, geom.y))
            elif props.get('type') == 'optimized_coverage':
                coverage_areas.append(geom)
        
        # 绘制原始配置
        self._plot_configuration(ax1, original_sensors, "原始传感器配置")
        
        # 绘制优化后配置
        self._plot_configuration_with_coverage(ax2, optimized_sensors, coverage_areas, "优化后传感器配置")
        
        # 添加标题信息
        props = optimization_geojson.get('properties', {})
        initial_coverage = props.get('initial_coverage_ratio', 0) * 100
        final_coverage = props.get('final_coverage_ratio', 0) * 100
        improvement = props.get('improvement', 0) * 100
        
        fig.suptitle(f'{title}\n'
                    f'传感器数量: {len(optimized_sensors)}, '
                    f'初始覆盖率: {initial_coverage:.1f}%, '
                    f'优化后覆盖率: {final_coverage:.1f}%, '
                    f'改进: +{improvement:.1f}%', 
                    fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.show()
    
    def _plot_configuration(self, ax, sensors: List[Tuple[float, float]], title: str):
        """绘制传感器配置"""
        # 绘制目标区域
        if self.target_area.geom_type == 'Polygon':
            x, y = self.target_area.exterior.xy
            ax.plot(x, y, 'b-', linewidth=2)
            ax.fill(x, y, alpha=0.2, color='lightblue')
        
        # 绘制传感器
        for i, (x, y) in enumerate(sensors):
            ax.scatter(x, y, c='red', s=80, marker='o', 
                      edgecolors='black', linewidth=1, zorder=5)
            ax.annotate(f'S{i}', (x, y), xytext=(5, 5), 
                       textcoords='offset points')
        
        ax.set_title(title, fontweight='bold')
        ax.set_xlabel('X 坐标 (km)')
        ax.set_ylabel('Y 坐标 (km)')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
    
    def _plot_configuration_with_coverage(self, ax, sensors: List[Tuple[float, float]], 
                                        coverage_areas: List, title: str):
        """绘制带覆盖区域的传感器配置"""
        # 绘制目标区域
        if self.target_area.geom_type == 'Polygon':
            x, y = self.target_area.exterior.xy
            ax.plot(x, y, 'b-', linewidth=2)
            ax.fill(x, y, alpha=0.2, color='lightblue')
        
        # 绘制覆盖区域
        for coverage in coverage_areas:
            if coverage.geom_type == 'Polygon':
                x_coords, y_coords = coverage.exterior.xy
                ax.fill(x_coords, y_coords, alpha=0.3, color='green')
                ax.plot(x_coords, y_coords, color='green', linewidth=1)
        
        # 绘制传感器
        for i, (x, y) in enumerate(sensors):
            ax.scatter(x, y, c='red', s=80, marker='o', 
                      edgecolors='black', linewidth=1, zorder=5)
            ax.annotate(f'S{i}', (x, y), xytext=(5, 5), 
                       textcoords='offset points')
        
        ax.set_title(title, fontweight='bold')
        ax.set_xlabel('X 坐标 (km)')
        ax.set_ylabel('Y 坐标 (km)')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')

def create_test_existing_sensors_geojson() -> Dict[str, Any]:
    """创建测试用的现有传感器GeoJSON"""
    existing_sensors = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [2, 2]
                },
                "properties": {
                    "id": 0,
                    "sensor_type": "ground_sensor",
                    "status": "existing"
                }
            },
            {
                "type": "Feature", 
                "geometry": {
                    "type": "Point",
                    "coordinates": [6, 2]
                },
                "properties": {
                    "id": 1,
                    "sensor_type": "ground_sensor",
                    "status": "existing"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point", 
                    "coordinates": [2, 6]
                },
                "properties": {
                    "id": 2,
                    "sensor_type": "ground_sensor",
                    "status": "existing"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [6, 6]
                },
                "properties": {
                    "id": 3,
                    "sensor_type": "ground_sensor", 
                    "status": "existing"
                }
            }
        ]
    }
    return existing_sensors

def demo_geojson_ground_sensor_position_optimize():
    """演示GeoJSON格式的地面传感器位置优化"""
    print("="*60)
    print("GeoJSON格式地面传感器位置优化演示")
    print("="*60)
    
    # 创建测试输入
    from geojson_ground_sensor_from_scratch import create_test_geojson
    target_area_geojson = create_test_geojson()
    existing_sensors_geojson = create_test_existing_sensors_geojson()
    sensor_radius = 2.0
    
    print("输入参数:")
    print(f"- 目标区域: {target_area_geojson['properties']['description']}")
    print(f"- 现有传感器数量: {len(existing_sensors_geojson['features'])}")
    print(f"- 传感器半径: {sensor_radius} km")
    
    # 创建优化器
    optimizer = GeoJSONGroundSensorPositionOptimizer(
        target_area_geojson=target_area_geojson,
        existing_sensors_geojson=existing_sensors_geojson,
        sensor_radius=sensor_radius,
        grid_resolution=0.5
    )
    
    # 执行优化
    optimized_geojson, final_coverage, optimization_info = optimizer.optimize_positions(
        target_coverage_ratio=0.9,
        max_iterations=50
    )
    
    # 输出结果
    print(f"\n=== GeoJSON优化结果 ===")
    print(f"最终覆盖率: {final_coverage*100:.2f}%")
    print(f"优化迭代次数: {optimization_info['iterations']}")
    print(f"覆盖率改进: {optimization_info['improvement']*100:.2f}个百分点")
    print(f"GeoJSON要素数量: {len(optimized_geojson['features'])}")
    
    # 导出GeoJSON文件
    output_filename = "ground_sensor_position_optimize_result.geojson"
    optimizer.export_results_geojson(output_filename, optimized_geojson)
    
    # 可视化结果（在测试环境中跳过）
    try:
        optimizer.visualize_optimization_geojson(optimized_geojson)
    except:
        print("跳过可视化（可能在无图形界面环境中运行）")
    
    # 显示部分GeoJSON内容
    print(f"\n=== GeoJSON示例内容 ===")
    print(json.dumps(optimized_geojson['properties'], indent=2, ensure_ascii=False))
    
    return optimizer, optimized_geojson

if __name__ == "__main__":
    demo_geojson_ground_sensor_position_optimize()
