"""
地面传感器增补优化模块

该模块用于在现有地面传感器基础上，通过增加最少数量的新传感器
来达到目标覆盖率要求。

主要功能：
1. 评估现有传感器覆盖缺口
2. 智能选择新增传感器位置
3. 基于贪心策略的最少增补
4. 成本效益分析

作者：GeoSensingAPI
"""

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class GroundSensorAdditionOptimizer:
    """
    地面传感器增补优化器
    
    在现有传感器基础上，通过增加最少数量的传感器来达到目标覆盖率
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
    
    def _evaluate_station_layout(self, stations: List[Tuple[float, float]]) -> Tuple[float, set]:
        """
        评估给定传感器布局的覆盖率和覆盖点集合
        
        参数:
            stations: 传感器位置列表
            
        返回:
            覆盖率, 被覆盖的网格点索引集合
        """
        if not stations:
            return 0.0, set()
        
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
        
        return coverage_ratio, covered_points
    
    def _identify_coverage_gaps(self, existing_stations: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        识别覆盖缺口区域
        
        参数:
            existing_stations: 现有传感器位置列表
            
        返回:
            未覆盖区域的网格点列表
        """
        _, covered_points = self._evaluate_station_layout(existing_stations)
        
        uncovered_points = []
        for i, point in enumerate(self.grid_points):
            if i not in covered_points:
                uncovered_points.append(point)
        
        return uncovered_points
    
    def _get_candidate_positions(self, existing_stations: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        生成候选传感器位置（避免与现有传感器重叠）
        
        参数:
            existing_stations: 现有传感器位置
            
        返回:
            候选位置列表
        """
        candidates = []
        minx, miny, maxx, maxy = self.target_area.bounds
        
        candidate_resolution = self.grid_resolution * 2
        x_coords = np.arange(minx, maxx + candidate_resolution, candidate_resolution)
        y_coords = np.arange(miny, maxy + candidate_resolution, candidate_resolution)
        
        min_distance = self.sensor_radius * 0.5  # 最小距离为半径的一半
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                candidate_pos = (x, y)
                
                # 检查是否在目标区域内或附近
                if (self.target_area.contains(point) or 
                    self.target_area.distance(point) <= self.sensor_radius):
                    
                    # 检查是否与现有传感器太近
                    too_close = False
                    for existing_pos in existing_stations:
                        distance = Point(candidate_pos).distance(Point(existing_pos))
                        if distance < min_distance:
                            too_close = True
                            break
                    
                    if not too_close:
                        candidates.append(candidate_pos)
                    
        return candidates
    
    def _calculate_coverage_gain(self, candidate_pos: Tuple[float, float], 
                               current_stations: List[Tuple[float, float]]) -> int:
        """
        计算在候选位置增加传感器能带来的覆盖增益
        
        参数:
            candidate_pos: 候选传感器位置
            current_stations: 当前传感器位置列表
            
        返回:
            新增覆盖的网格点数量
        """
        # 计算当前覆盖情况
        _, current_covered = self._evaluate_station_layout(current_stations)
        
        # 计算增加新传感器后的覆盖情况
        new_stations = current_stations + [candidate_pos]
        _, new_covered = self._evaluate_station_layout(new_stations)
        
        # 返回新增覆盖的点数
        return len(new_covered - current_covered)
    
    def optimize_with_additions(self, existing_stations: List[Tuple[float, float]], 
                              target_coverage_ratio: float,
                              max_additional_stations: int = 10) -> Tuple[List[Tuple[float, float]], float, Dict]:
        """
        通过新增传感器优化覆盖率
        
        参数:
            existing_stations: 现有传感器位置列表
            target_coverage_ratio: 目标覆盖率
            max_additional_stations: 最大可新增传感器数量
            
        返回:
            最终传感器位置列表, 实际覆盖率, 优化统计信息
        """
        if not existing_stations:
            raise ValueError("传感器位置列表不能为空")
        
        print(f"开始新增传感器优化方案...")
        print(f"现有传感器数量: {len(existing_stations)}")
        print(f"目标覆盖率: {target_coverage_ratio*100:.1f}%")
        print(f"最大可新增传感器: {max_additional_stations}")
        
        # 评估初始状态
        initial_coverage, _ = self._evaluate_station_layout(existing_stations)
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        
        if initial_coverage >= target_coverage_ratio:
            print(f"初始方案已满足目标覆盖率")
            return existing_stations, initial_coverage, {
                '初始覆盖率': f"{initial_coverage*100:.2f}%",
                '最终覆盖率': f"{initial_coverage*100:.2f}%",
                '新增传感器数量': 0,
                '最终传感器数量': len(existing_stations),
                '是否达到目标': "是",
                '新增传感器位置': []
            }
        
        # 当前传感器配置
        current_stations = existing_stations.copy()
        current_coverage = initial_coverage
        
        added_stations = []
        optimization_history = []
        
        for addition_count in range(max_additional_stations):
            if current_coverage >= target_coverage_ratio:
                print(f"达到目标覆盖率，停止增补")
                break
            
            # 获取候选位置
            candidates = self._get_candidate_positions(current_stations)
            
            if not candidates:
                print(f"无可用的增补候选位置，停止优化")
                break
            
            # 选择最佳候选位置（贪心策略：选择覆盖增益最大的位置）
            best_position = None
            best_gain = 0
            
            for candidate_pos in candidates:
                gain = self._calculate_coverage_gain(candidate_pos, current_stations)
                if gain > best_gain:
                    best_gain = gain
                    best_position = candidate_pos
            
            if best_position is None or best_gain == 0:
                print(f"无法找到有效的新增位置，停止增补")
                break
            
            # 添加选中的传感器
            current_stations.append(best_position)
            added_stations.append(best_position)
            current_coverage, _ = self._evaluate_station_layout(current_stations)
            
            print(f"增补传感器 {addition_count + 1}: {best_position}, "
                  f"覆盖增益: {best_gain} 点, "
                  f"覆盖率: {current_coverage*100:.2f}%")
            
            optimization_history.append({
                'added_station': best_position,
                'coverage_gain': best_gain,
                'coverage': current_coverage,
                'total_stations': len(current_stations)
            })
        
        # 准备统计信息
        optimization_stats = {
            '初始覆盖率': f"{initial_coverage*100:.2f}%",
            '最终覆盖率': f"{current_coverage*100:.2f}%",
            '覆盖率提升': f"{(current_coverage-initial_coverage)*100:.2f}%",
            '原有传感器数量': len(existing_stations),
            '新增传感器数量': len(added_stations),
            '最终传感器数量': len(current_stations),
            '目标覆盖率': f"{target_coverage_ratio*100:.1f}%",
            '是否达到目标': "是" if current_coverage >= target_coverage_ratio else "否",
            '新增传感器位置': added_stations,
            '优化历史': optimization_history
        }
        
        print(f"\n增补优化完成!")
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"最终覆盖率: {current_coverage*100:.2f}%")
        print(f"新增传感器数量: {len(added_stations)}")
        print(f"总传感器数量: {len(current_stations)}")
        
        return current_stations, current_coverage, optimization_stats
    
    def visualize_addition_result(self, original_stations: List[Tuple[float, float]], 
                                final_stations: List[Tuple[float, float]],
                                added_stations: List[Tuple[float, float]],
                                title: str = "地面传感器增补优化结果"):
        """可视化增补结果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 计算覆盖率
        original_coverage, _ = self._evaluate_station_layout(original_stations)
        final_coverage, _ = self._evaluate_station_layout(final_stations)
        
        # 绘制原始方案
        self._plot_stations(ax1, original_stations, [], 
                           f"原始方案 (覆盖率: {original_coverage*100:.1f}%)")
        
        # 绘制增补方案
        self._plot_stations(ax2, original_stations, added_stations,
                           f"增补方案 (覆盖率: {final_coverage*100:.1f}%)")
        
        plt.suptitle(f"{title}\n"
                    f"新增传感器: {len(added_stations)} 个 | "
                    f"覆盖率提升: {(final_coverage-original_coverage)*100:.1f}%", fontsize=14)
        plt.tight_layout()
        plt.show()
    
    def _plot_stations(self, ax, original_stations: List[Tuple[float, float]], 
                      added_stations: List[Tuple[float, float]], title: str):
        """绘制传感器布局"""
        # 绘制目标区域
        x_coords, y_coords = zip(*self.target_area_coords)
        ax.plot(list(x_coords) + [x_coords[0]], 
                list(y_coords) + [y_coords[0]], 
                'b-', linewidth=2, label='目标区域')
        ax.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
        
        # 绘制原有传感器
        for i, station in enumerate(original_stations):
            circle = plt.Circle(station, self.sensor_radius, 
                              fill=False, color='green', alpha=0.6, linewidth=1)
            ax.add_patch(circle)
            circle_fill = plt.Circle(station, self.sensor_radius, 
                                   fill=True, color='green', alpha=0.15)
            ax.add_patch(circle_fill)
            
            ax.plot(station[0], station[1], 'go', markersize=8)
            ax.text(station[0], station[1] + self.sensor_radius + 0.2, f'G{i+1}', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='green', alpha=0.7))
        
        # 绘制新增传感器
        for i, station in enumerate(added_stations):
            circle = plt.Circle(station, self.sensor_radius, 
                              fill=False, color='red', alpha=0.8, linewidth=2)
            ax.add_patch(circle)
            circle_fill = plt.Circle(station, self.sensor_radius, 
                                   fill=True, color='red', alpha=0.25)
            ax.add_patch(circle_fill)
            
            ax.plot(station[0], station[1], 'ro', markersize=10)
            ax.text(station[0], station[1] + self.sensor_radius + 0.2, f'N{i+1}', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='red', alpha=0.8))
        
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
    
    def analyze_cost_effectiveness(self, original_stations: List[Tuple[float, float]], 
                                 final_stations: List[Tuple[float, float]],
                                 added_stations: List[Tuple[float, float]], 
                                 cost_per_sensor: float = 1.0) -> Dict:
        """
        分析增补方案的成本效益
        
        参数:
            original_stations: 原始传感器位置
            final_stations: 最终传感器位置  
            added_stations: 新增传感器位置
            cost_per_sensor: 每个传感器的成本
            
        返回:
            成本效益分析结果
        """
        original_coverage, _ = self._evaluate_station_layout(original_stations)
        final_coverage, _ = self._evaluate_station_layout(final_stations)
        
        coverage_improvement = final_coverage - original_coverage
        total_cost = len(added_stations) * cost_per_sensor
        cost_effectiveness = coverage_improvement / total_cost if total_cost > 0 else 0
        
        return {
            '原始覆盖率': f"{original_coverage*100:.2f}%",
            '最终覆盖率': f"{final_coverage*100:.2f}%",
            '覆盖率提升': f"{coverage_improvement*100:.2f}%",
            '新增传感器数量': len(added_stations),
            '总增补成本': f"{total_cost:.1f}",
            '成本效益比': f"{cost_effectiveness:.4f}",
            '单位成本覆盖提升': f"{(coverage_improvement/len(added_stations))*100:.2f}%" if added_stations else "0%"
        }


def demo_ground_sensor_addition_optimize():
    """演示地面传感器增补优化"""
    print("="*60)
    print("地面传感器增补优化演示")
    print("="*60)
    
    # 创建目标区域
    target_area_coords = [(0, 0), (15, 0), (15, 12), (0, 12)]
    sensor_radius = 2.8
    
    # 创建一个覆盖不足的现有传感器布局
    existing_stations = [
        (3, 3),
        (8, 2),
        (12, 8),
        (4, 9)
    ]
    
    target_coverage = 0.85  # 目标85%覆盖率
    
    print(f"目标区域: {target_area_coords}")
    print(f"传感器半径: {sensor_radius}")
    print(f"现有传感器: {len(existing_stations)} 个")
    print(f"目标覆盖率: {target_coverage*100}%")
    
    # 创建优化器
    optimizer = GroundSensorAdditionOptimizer(
        target_area_coords=target_area_coords,
        sensor_radius=sensor_radius,
        grid_resolution=0.4
    )
    
    # 评估原始方案
    original_coverage, _ = optimizer._evaluate_station_layout(existing_stations)
    print(f"原始覆盖率: {original_coverage*100:.2f}%")
    
    # 进行增补优化
    final_stations, final_coverage, stats = optimizer.optimize_with_additions(
        existing_stations=existing_stations,
        target_coverage_ratio=target_coverage,
        max_additional_stations=6
    )
    
    # 获取新增传感器
    added_stations = stats['新增传感器位置']
    
    # 显示优化结果
    print(f"\n增补优化结果:")
    print(f"最终传感器数量: {len(final_stations)}")
    print(f"新增传感器数量: {len(added_stations)}")
    print(f"最终覆盖率: {final_coverage*100:.2f}%")
    print(f"是否达到目标: {stats['是否达到目标']}")
    
    # 成本效益分析
    cost_analysis = optimizer.analyze_cost_effectiveness(
        existing_stations, final_stations, added_stations, cost_per_sensor=10.0
    )
    
    print(f"\n成本效益分析:")
    for key, value in cost_analysis.items():
        print(f"  {key}: {value}")
    
    # 可视化结果
    optimizer.visualize_addition_result(
        existing_stations, final_stations, added_stations
    )
    
    return optimizer, final_stations, stats


if __name__ == "__main__":
    demo_ground_sensor_addition_optimize()