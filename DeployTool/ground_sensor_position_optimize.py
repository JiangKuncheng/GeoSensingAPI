"""
地面传感器位置优化模块

该模块用于优化已有地面传感器的位置布设，在不增加传感器数量的情况下
通过重新配置传感器位置来提高覆盖率。

主要功能：
1. 评估现有传感器布设方案
2. 基于局部搜索的位置优化
3. 覆盖率提升分析
4. 优化前后对比可视化

作者：GeoSensingAPI
"""

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from typing import List, Tuple, Dict
import random
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class GroundSensorPositionOptimizer:
    """
    地面传感器位置优化器
    
    在不改变传感器数量的情况下，通过调整位置来优化覆盖率
    """
    
    def __init__(self, target_area_coords: List[Tuple[float, float]], 
                 sensor_radius: float, grid_resolution: float = 0.5):
        """
        初始化优化器
        
        参数:
            target_area_coords: 目标区域的坐标点列表
            sensor_radius: 传感器观测半径
            grid_resolution: 网格分辨率
        """
        self.target_area_coords = target_area_coords
        self.sensor_radius = sensor_radius
        self.grid_resolution = grid_resolution
        
        # 创建目标区域的多边形
        self.target_area = Polygon(target_area_coords)
        
        # 初始化网格点
        self.grid_points = []
        self._initialize_grid()
        
    def _initialize_grid(self):
        """初始化目标区域的网格点"""
        minx, miny, maxx, maxy = self.target_area.bounds
        
        x_coords = np.arange(minx, maxx + self.grid_resolution, self.grid_resolution)
        y_coords = np.arange(miny, maxy + self.grid_resolution, self.grid_resolution)
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point) or self.target_area.touches(point):
                    self.grid_points.append((x, y))
        
        print(f"网格初始化完成，共生成 {len(self.grid_points)} 个网格点")
    
    def _evaluate_station_layout(self, stations: List[Tuple[float, float]]) -> float:
        """
        评估给定传感器布局的覆盖率
        
        参数:
            stations: 传感器位置列表
            
        返回:
            覆盖率 (0-1之间)
        """
        if not stations:
            return 0.0
        
        # 计算被覆盖的网格点
        covered_points = set()
        
        for station_pos in stations:
            station_point = Point(station_pos)
            
            for i, grid_point in enumerate(self.grid_points):
                grid_point_geom = Point(grid_point)
                if station_point.distance(grid_point_geom) <= self.sensor_radius:
                    covered_points.add(i)
        
        # 计算覆盖率
        total_points = len(self.grid_points)
        coverage_ratio = len(covered_points) / total_points if total_points > 0 else 0.0
        
        return coverage_ratio
    
    def _get_candidate_positions(self) -> List[Tuple[float, float]]:
        """生成候选传感器位置"""
        candidates = []
        minx, miny, maxx, maxy = self.target_area.bounds
        
        candidate_resolution = self.grid_resolution * 2
        x_coords = np.arange(minx, maxx + candidate_resolution, candidate_resolution)
        y_coords = np.arange(miny, maxy + candidate_resolution, candidate_resolution)
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if (self.target_area.contains(point) or 
                    self.target_area.distance(point) <= self.sensor_radius):
                    candidates.append((x, y))
                    
        return candidates
    
    def optimize_positions(self, existing_stations: List[Tuple[float, float]], 
                         target_coverage_ratio: float = None,
                         max_iterations: int = 100) -> Tuple[List[Tuple[float, float]], float, Dict]:
        """
        优化已有传感器布设方案（不增加传感器数量）
        
        参数:
            existing_stations: 现有传感器位置列表 [(x1,y1), (x2,y2), ...]
            target_coverage_ratio: 目标覆盖率，如果为None则最大化覆盖率
            max_iterations: 最大优化迭代次数
            
        返回:
            优化后的传感器位置, 实际覆盖率, 优化统计信息
        """
        if not existing_stations:
            raise ValueError("传感器位置列表不能为空")
        
        print(f"开始优化现有传感器位置...")
        print(f"传感器数量: {len(existing_stations)} (固定不变)")
        print(f"观测半径: {self.sensor_radius}")
        if target_coverage_ratio:
            print(f"目标覆盖率: {target_coverage_ratio*100:.1f}%")
        
        # 评估初始方案
        initial_coverage = self._evaluate_station_layout(existing_stations)
        print(f"初始方案覆盖率: {initial_coverage*100:.2f}%")
        
        # 初始化优化
        current_stations = existing_stations.copy()
        current_coverage = initial_coverage
        best_stations = current_stations.copy()
        best_coverage = current_coverage
        
        # 获取候选位置
        candidate_positions = self._get_candidate_positions()
        
        optimization_history = []
        no_improvement_count = 0
        
        for iteration in range(max_iterations):
            improved = False
            
            # 尝试移动每个传感器到更好的位置
            for station_idx in range(len(current_stations)):
                best_new_position = None
                best_new_coverage = current_coverage
                
                # 保存当前传感器位置
                original_position = current_stations[station_idx]
                
                # 尝试将当前传感器移动到每个候选位置
                for new_pos in candidate_positions:
                    # 临时移动传感器
                    current_stations[station_idx] = new_pos
                    
                    # 评估新布局的覆盖率
                    new_coverage = self._evaluate_station_layout(current_stations)
                    
                    # 如果找到更好的位置
                    if new_coverage > best_new_coverage:
                        best_new_coverage = new_coverage
                        best_new_position = new_pos
                
                # 如果找到改进
                if best_new_position is not None:
                    current_stations[station_idx] = best_new_position
                    current_coverage = best_new_coverage
                    improved = True
                    
                    print(f"迭代 {iteration+1}: 移动传感器 {station_idx+1} "
                          f"从 {original_position} 到 {best_new_position}, "
                          f"覆盖率: {current_coverage*100:.2f}%")
                else:
                    # 恢复原位置
                    current_stations[station_idx] = original_position
            
            # 记录优化历史
            optimization_history.append({
                'iteration': iteration + 1,
                'coverage': current_coverage,
                'stations': current_stations.copy()
            })
            
            # 更新最佳方案
            if current_coverage > best_coverage:
                best_coverage = current_coverage
                best_stations = current_stations.copy()
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # 检查收敛条件
            if not improved:
                print(f"在迭代 {iteration+1} 没有找到改进，优化结束")
                break
            
            # 如果连续多次没有改进，提前结束
            if no_improvement_count >= 10:
                print(f"连续 {no_improvement_count} 次迭代无改进，优化结束")
                break
            
            # 如果已达到目标覆盖率
            if target_coverage_ratio and current_coverage >= target_coverage_ratio:
                print(f"已达到目标覆盖率 {target_coverage_ratio*100:.1f}%，优化结束")
                break
        
        # 准备优化统计信息
        optimization_stats = {
            '初始覆盖率': f"{initial_coverage*100:.2f}%",
            '优化后覆盖率': f"{best_coverage*100:.2f}%",
            '覆盖率提升': f"{(best_coverage-initial_coverage)*100:.2f}%",
            '传感器数量': len(existing_stations),
            '目标覆盖率': f"{target_coverage_ratio*100:.1f}%" if target_coverage_ratio else "最大化覆盖率",
            '是否达到目标': "是" if (not target_coverage_ratio or best_coverage >= target_coverage_ratio) else "否",
            '优化迭代次数': len(optimization_history),
            '优化历史': optimization_history
        }
        
        print(f"\n位置优化完成!")
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"优化后覆盖率: {best_coverage*100:.2f}%")
        print(f"覆盖率提升: {(best_coverage-initial_coverage)*100:.2f}%")
        
        return best_stations, best_coverage, optimization_stats
    
    def visualize_optimization(self, original_stations: List[Tuple[float, float]], 
                             optimized_stations: List[Tuple[float, float]],
                             title: str = "地面传感器位置优化结果"):
        """可视化优化结果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        # 计算覆盖率
        original_coverage = self._evaluate_station_layout(original_stations)
        optimized_coverage = self._evaluate_station_layout(optimized_stations)
        
        # 绘制原始方案
        self._plot_stations(ax1, original_stations, 
                           f"原始方案 (覆盖率: {original_coverage*100:.1f}%)")
        
        # 绘制优化方案
        self._plot_stations(ax2, optimized_stations, 
                           f"优化方案 (覆盖率: {optimized_coverage*100:.1f}%)")
        
        plt.suptitle(f"{title}\n改进: {(optimized_coverage-original_coverage)*100:.1f}%", 
                    fontsize=14)
        plt.tight_layout()
        plt.show()
    
    def _plot_stations(self, ax, stations: List[Tuple[float, float]], title: str):
        """绘制传感器布局"""
        # 绘制目标区域
        x_coords, y_coords = zip(*self.target_area_coords)
        ax.plot(list(x_coords) + [x_coords[0]], 
                list(y_coords) + [y_coords[0]], 
                'b-', linewidth=2, label='目标区域')
        ax.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
        
        # 绘制传感器覆盖
        for i, station in enumerate(stations):
            circle = plt.Circle(station, self.sensor_radius, 
                              fill=False, color='green', alpha=0.7, linewidth=1.5)
            ax.add_patch(circle)
            
            circle_fill = plt.Circle(station, self.sensor_radius, 
                                   fill=True, color='green', alpha=0.2)
            ax.add_patch(circle_fill)
            
            # 标注传感器
            ax.scatter(station[0], station[1], c='green', s=80, 
                      marker='o', edgecolors='black', linewidth=1, zorder=5)
            ax.text(station[0], station[1] + self.sensor_radius + 0.3, f'{i+1}', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='green', alpha=0.7))
        
        ax.set_xlabel('X 坐标')
        ax.set_ylabel('Y 坐标')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # 设置坐标轴范围
        minx, miny, maxx, maxy = self.target_area.bounds
        margin = self.sensor_radius * 0.5
        ax.set_xlim(minx - margin, maxx + margin)
        ax.set_ylim(miny - margin, maxy + margin)
    
    def compare_layouts(self, original_stations: List[Tuple[float, float]], 
                       optimized_stations: List[Tuple[float, float]]) -> Dict:
        """
        比较原始和优化后的传感器布局
        
        参数:
            original_stations: 原始传感器位置
            optimized_stations: 优化后传感器位置
            
        返回:
            详细比较结果
        """
        original_coverage = self._evaluate_station_layout(original_stations)
        optimized_coverage = self._evaluate_station_layout(optimized_stations)
        
        improvement = optimized_coverage - original_coverage
        
        return {
            '原始方案': {
                '覆盖率': f"{original_coverage*100:.2f}%",
                '传感器数量': len(original_stations),
                '传感器位置': original_stations
            },
            '优化方案': {
                '覆盖率': f"{optimized_coverage*100:.2f}%",
                '传感器数量': len(optimized_stations),
                '传感器位置': optimized_stations
            },
            '改进效果': {
                '覆盖率提升': f"{improvement*100:.2f}%",
                '相对提升': f"{(improvement/original_coverage)*100:.2f}%" if original_coverage > 0 else "N/A",
                '是否有改进': "是" if improvement > 0 else "否"
            }
        }


def demo_ground_sensor_position_optimize():
    """演示地面传感器位置优化"""
    print("="*60)
    print("地面传感器位置优化演示")
    print("="*60)
    
    # 创建目标区域
    target_area_coords = [(0, 0), (12, 0), (12, 10), (0, 10)]
    sensor_radius = 2.5
    
    # 创建一个次优的现有传感器布局
    existing_stations = [
        (2, 2),
        (6, 3),
        (10, 2),
        (3, 7),
        (9, 8)
    ]
    
    print(f"目标区域: {target_area_coords}")
    print(f"传感器半径: {sensor_radius}")
    print(f"现有传感器位置: {existing_stations}")
    
    # 创建优化器
    optimizer = GroundSensorPositionOptimizer(
        target_area_coords=target_area_coords,
        sensor_radius=sensor_radius,
        grid_resolution=0.4
    )
    
    # 评估原始方案
    original_coverage = optimizer._evaluate_station_layout(existing_stations)
    print(f"原始方案覆盖率: {original_coverage*100:.2f}%")
    
    # 进行位置优化
    optimized_stations, final_coverage, stats = optimizer.optimize_positions(
        existing_stations=existing_stations,
        target_coverage_ratio=0.85,  # 目标85%覆盖率
        max_iterations=50
    )
    
    # 显示优化结果
    print(f"\n优化结果:")
    print(f"优化后传感器位置: {optimized_stations}")
    print(f"最终覆盖率: {final_coverage*100:.2f}%")
    
    # 详细比较
    comparison = optimizer.compare_layouts(existing_stations, optimized_stations)
    print(f"\n详细比较:")
    print(f"原始覆盖率: {comparison['原始方案']['覆盖率']}")
    print(f"优化覆盖率: {comparison['优化方案']['覆盖率']}")
    print(f"覆盖率提升: {comparison['改进效果']['覆盖率提升']}")
    print(f"相对提升: {comparison['改进效果']['相对提升']}")
    
    # 可视化结果
    optimizer.visualize_optimization(existing_stations, optimized_stations)
    
    return optimizer, optimized_stations, stats


if __name__ == "__main__":
    demo_ground_sensor_position_optimize()