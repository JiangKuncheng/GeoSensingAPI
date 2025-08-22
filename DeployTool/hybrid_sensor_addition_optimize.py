"""
卫星+地面混合传感器增补优化模块

该模块用于在现有卫星和地面传感器基础上，通过增加最少数量的新传感器
（卫星或地面传感器）来达到目标覆盖率要求。

主要功能：
1. 评估现有混合传感器覆盖缺口
2. 智能选择最优增补传感器类型和配置
3. 基于成本效益的混合增补策略
4. 卫星vs地面传感器增补决策分析

作者：GeoSensingAPI
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point
from typing import List, Tuple, Dict
import random
import math
import time
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

@dataclass
class Satellite:
    """卫星传感器类"""
    id: int
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    swath_width: float
    cost: float = 100.0
    
    def get_coverage_area(self) -> Polygon:
        """获取卫星覆盖区域的多边形（条带状）"""
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0:
            half_width = self.swath_width / 2
            return Polygon([
                (self.start_x - half_width, self.start_y - half_width),
                (self.start_x + half_width, self.start_y - half_width),
                (self.start_x + half_width, self.start_y + half_width),
                (self.start_x - half_width, self.start_y + half_width)
            ])
        
        unit_dx = dx / length
        unit_dy = dy / length
        perp_dx = -unit_dy * self.swath_width / 2
        perp_dy = unit_dx * self.swath_width / 2
        
        vertices = [
            (self.start_x + perp_dx, self.start_y + perp_dy),
            (self.start_x - perp_dx, self.start_y - perp_dy),
            (self.end_x - perp_dx, self.end_y - perp_dy),
            (self.end_x + perp_dx, self.end_y + perp_dy)
        ]
        
        return Polygon(vertices)

@dataclass
class GroundSensor:
    """地面传感器类"""
    id: int
    x: float
    y: float
    radius: float
    cost: float = 10.0
    
    def get_coverage_area(self) -> Polygon:
        """获取地面传感器覆盖区域的多边形（圆形）"""
        return Point(self.x, self.y).buffer(self.radius)

@dataclass
class AdditionCandidate:
    """增补候选传感器"""
    sensor_type: str  # 'satellite' 或 'ground'
    position_params: Dict[str, float]  # 位置参数
    cost: float
    expected_coverage_gain: float
    cost_effectiveness: float  # 覆盖增益/成本

@dataclass
class HybridAdditionSolution:
    """混合传感器增补方案结果"""
    original_satellites: List[Satellite]
    original_ground_sensors: List[GroundSensor]
    added_satellites: List[Satellite]
    added_ground_sensors: List[GroundSensor]
    final_satellites: List[Satellite]
    final_ground_sensors: List[GroundSensor]
    original_coverage: float
    final_coverage: float
    target_coverage: float
    total_added_cost: float
    optimization_time: float
    achieved_target: bool
    cost_effectiveness_ratio: float

class HybridSensorAdditionOptimizer:
    """混合传感器增补优化器"""
    
    def __init__(self, target_area: Polygon, grid_resolution: float = 0.5):
        """
        初始化优化器
        
        参数:
            target_area: 目标覆盖区域
            grid_resolution: 网格分辨率
        """
        self.target_area = target_area
        self.grid_resolution = grid_resolution
        self.grid_points = self._generate_grid_points()
        
    def _generate_grid_points(self) -> List[Tuple[float, float]]:
        """生成覆盖计算的网格点"""
        minx, miny, maxx, maxy = self.target_area.bounds
        
        x_coords = np.arange(minx, maxx + self.grid_resolution, self.grid_resolution)
        y_coords = np.arange(miny, maxy + self.grid_resolution, self.grid_resolution)
        
        grid_points = []
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point) or self.target_area.touches(point):
                    grid_points.append((x, y))
        
        return grid_points
    
    def evaluate_deployment(self, satellites: List[Satellite], 
                          ground_sensors: List[GroundSensor]) -> Tuple[float, set]:
        """
        评估当前部署方案的覆盖率和覆盖点集合
        
        参数:
            satellites: 卫星列表
            ground_sensors: 地面传感器列表
            
        返回:
            覆盖率, 被覆盖的网格点索引集合
        """
        covered_points = set()
        
        # 计算卫星覆盖
        for satellite in satellites:
            satellite_coverage = satellite.get_coverage_area()
            for i, point in enumerate(self.grid_points):
                if satellite_coverage.contains(Point(point)):
                    covered_points.add(i)
        
        # 计算地面传感器覆盖
        for sensor in ground_sensors:
            sensor_point = Point(sensor.x, sensor.y)
            for i, point in enumerate(self.grid_points):
                if sensor_point.distance(Point(point)) <= sensor.radius:
                    covered_points.add(i)
        
        coverage_ratio = len(covered_points) / len(self.grid_points) if self.grid_points else 0.0
        return coverage_ratio, covered_points
    
    def identify_coverage_gaps(self, satellites: List[Satellite], 
                             ground_sensors: List[GroundSensor]) -> List[Tuple[float, float]]:
        """
        识别覆盖缺口区域
        
        参数:
            satellites: 现有卫星列表
            ground_sensors: 现有地面传感器列表
            
        返回:
            未覆盖区域的中心点列表
        """
        _, covered_points = self.evaluate_deployment(satellites, ground_sensors)
        
        uncovered_points = []
        for i, point in enumerate(self.grid_points):
            if i not in covered_points:
                uncovered_points.append(point)
        
        if not uncovered_points:
            return []
        
        # 使用聚类方法识别覆盖缺口的中心
        # 简化版本：直接返回未覆盖点，实际可以使用K-means等聚类算法
        return uncovered_points
    
    def generate_addition_candidates(self, satellites: List[Satellite], 
                                   ground_sensors: List[GroundSensor],
                                   max_satellite_cost: float = 100,
                                   max_ground_sensor_cost: float = 20) -> List[AdditionCandidate]:
        """
        生成增补候选传感器（包括卫星和地面传感器）
        
        参数:
            satellites: 现有卫星
            ground_sensors: 现有地面传感器
            max_satellite_cost: 卫星最大成本
            max_ground_sensor_cost: 地面传感器最大成本
            
        返回:
            候选增补传感器列表
        """
        candidates = []
        coverage_gaps = self.identify_coverage_gaps(satellites, ground_sensors)
        
        if not coverage_gaps:
            return candidates
        
        minx, miny, maxx, maxy = self.target_area.bounds
        
        # 为每个覆盖缺口生成候选传感器
        gap_centers = self._cluster_gaps(coverage_gaps)
        
        for center in gap_centers:
            # 候选地面传感器
            for radius in [1.5, 2.0, 2.5, 3.0]:
                cost = 8 + radius * 3  # 成本与半径相关
                if cost <= max_ground_sensor_cost:
                    expected_gain = self._estimate_coverage_gain_ground(
                        center[0], center[1], radius, satellites, ground_sensors
                    )
                    
                    if expected_gain > 0:
                        candidates.append(AdditionCandidate(
                            sensor_type='ground',
                            position_params={'x': center[0], 'y': center[1], 'radius': radius},
                            cost=cost,
                            expected_coverage_gain=expected_gain,
                            cost_effectiveness=expected_gain / cost
                        ))
            
            # 候选卫星（通过覆盖缺口的轨道）
            for swath_width in [2.0, 2.5, 3.0, 3.5]:
                # 生成通过缺口中心的不同方向轨道
                for angle in [0, 45, 90, 135]:  # 不同轨道倾角
                    angle_rad = np.radians(angle)
                    
                    # 计算轨道起止点
                    if angle == 0 or angle == 180:  # 南北向
                        start_x = center[0]
                        start_y = miny
                        end_x = center[0]
                        end_y = maxy
                    elif angle == 90:  # 东西向
                        start_x = minx
                        start_y = center[1]
                        end_x = maxx
                        end_y = center[1]
                    else:  # 斜向
                        # 简化处理，生成通过中心点的斜向轨道
                        length = min(maxx - minx, maxy - miny)
                        dx = length * np.cos(angle_rad) / 2
                        dy = length * np.sin(angle_rad) / 2
                        start_x = max(minx, center[0] - dx)
                        start_y = max(miny, center[1] - dy)
                        end_x = min(maxx, center[0] + dx)
                        end_y = min(maxy, center[1] + dy)
                    
                    cost = 70 + swath_width * 8  # 成本与轨道宽度相关
                    if cost <= max_satellite_cost:
                        expected_gain = self._estimate_coverage_gain_satellite(
                            start_x, start_y, end_x, end_y, swath_width, 
                            satellites, ground_sensors
                        )
                        
                        if expected_gain > 0:
                            candidates.append(AdditionCandidate(
                                sensor_type='satellite',
                                position_params={
                                    'start_x': start_x, 'start_y': start_y,
                                    'end_x': end_x, 'end_y': end_y,
                                    'swath_width': swath_width
                                },
                                cost=cost,
                                expected_coverage_gain=expected_gain,
                                cost_effectiveness=expected_gain / cost
                            ))
        
        # 按成本效益排序
        candidates.sort(key=lambda x: x.cost_effectiveness, reverse=True)
        return candidates
    
    def _cluster_gaps(self, gaps: List[Tuple[float, float]], 
                     max_clusters: int = 5) -> List[Tuple[float, float]]:
        """
        将覆盖缺口聚类，找到主要的缺口中心
        
        参数:
            gaps: 未覆盖点列表
            max_clusters: 最大聚类数
            
        返回:
            聚类中心点列表
        """
        if len(gaps) <= max_clusters:
            return gaps
        
        # 简化版本：随机采样代表性点
        # 实际可以使用K-means聚类
        np.random.seed(42)
        selected_indices = np.random.choice(len(gaps), max_clusters, replace=False)
        return [gaps[i] for i in selected_indices]
    
    def _estimate_coverage_gain_ground(self, x: float, y: float, radius: float,
                                     existing_satellites: List[Satellite],
                                     existing_ground_sensors: List[GroundSensor]) -> float:
        """估算地面传感器的覆盖增益"""
        # 创建临时传感器
        temp_sensor = GroundSensor(-1, x, y, radius, 0)
        
        # 计算添加前后的覆盖差异
        original_coverage, _ = self.evaluate_deployment(existing_satellites, existing_ground_sensors)
        new_coverage, _ = self.evaluate_deployment(existing_satellites, 
                                                  existing_ground_sensors + [temp_sensor])
        
        return new_coverage - original_coverage
    
    def _estimate_coverage_gain_satellite(self, start_x: float, start_y: float,
                                        end_x: float, end_y: float, swath_width: float,
                                        existing_satellites: List[Satellite],
                                        existing_ground_sensors: List[GroundSensor]) -> float:
        """估算卫星的覆盖增益"""
        # 创建临时卫星
        temp_satellite = Satellite(-1, start_x, start_y, end_x, end_y, swath_width, 0)
        
        # 计算添加前后的覆盖差异
        original_coverage, _ = self.evaluate_deployment(existing_satellites, existing_ground_sensors)
        new_coverage, _ = self.evaluate_deployment(existing_satellites + [temp_satellite], 
                                                  existing_ground_sensors)
        
        return new_coverage - original_coverage
    
    def optimize_additions_greedy(self, satellites: List[Satellite], 
                                ground_sensors: List[GroundSensor],
                                target_coverage: float,
                                max_budget: float = float('inf'),
                                max_additions: int = 10) -> HybridAdditionSolution:
        """
        使用贪心算法优化混合传感器增补方案
        
        参数:
            satellites: 现有卫星
            ground_sensors: 现有地面传感器
            target_coverage: 目标覆盖率
            max_budget: 最大预算
            max_additions: 最大增补数量
            
        返回:
            增补优化结果
        """
        print(f"开始贪心混合传感器增补优化...")
        print(f"目标覆盖率: {target_coverage*100:.1f}%")
        print(f"最大预算: {max_budget}")
        
        start_time = time.time()
        
        # 评估原始方案
        original_coverage, _ = self.evaluate_deployment(satellites, ground_sensors)
        print(f"原始覆盖率: {original_coverage*100:.2f}%")
        
        if original_coverage >= target_coverage:
            print(f"原始方案已满足目标覆盖率")
            return self._create_no_addition_solution(satellites, ground_sensors, 
                                                   target_coverage, start_time)
        
        # 当前传感器配置
        current_satellites = satellites.copy()
        current_ground_sensors = ground_sensors.copy()
        current_coverage = original_coverage
        
        added_satellites = []
        added_ground_sensors = []
        total_cost = 0
        
        for iteration in range(max_additions):
            if current_coverage >= target_coverage:
                print(f"达到目标覆盖率，停止增补")
                break
            
            # 生成当前状态下的候选增补
            candidates = self.generate_addition_candidates(
                current_satellites, current_ground_sensors
            )
            
            if not candidates:
                print(f"无可用的增补候选，停止优化")
                break
            
            # 选择最佳候选（成本效益最高且在预算内）
            best_candidate = None
            for candidate in candidates:
                if total_cost + candidate.cost <= max_budget:
                    best_candidate = candidate
                    break
            
            if best_candidate is None:
                print(f"预算不足，无法继续增补")
                break
            
            # 添加选中的传感器
            if best_candidate.sensor_type == 'satellite':
                new_id = len(current_satellites) + len(added_satellites)
                new_satellite = Satellite(
                    new_id,
                    best_candidate.position_params['start_x'],
                    best_candidate.position_params['start_y'],
                    best_candidate.position_params['end_x'],
                    best_candidate.position_params['end_y'],
                    best_candidate.position_params['swath_width'],
                    best_candidate.cost
                )
                current_satellites.append(new_satellite)
                added_satellites.append(new_satellite)
                
            else:  # ground sensor
                new_id = len(current_ground_sensors) + len(added_ground_sensors)
                new_sensor = GroundSensor(
                    new_id,
                    best_candidate.position_params['x'],
                    best_candidate.position_params['y'],
                    best_candidate.position_params['radius'],
                    best_candidate.cost
                )
                current_ground_sensors.append(new_sensor)
                added_ground_sensors.append(new_sensor)
            
            total_cost += best_candidate.cost
            current_coverage, _ = self.evaluate_deployment(current_satellites, current_ground_sensors)
            
            print(f"增补 {iteration+1}: {best_candidate.sensor_type}, "
                  f"成本: {best_candidate.cost:.1f}, "
                  f"覆盖率: {current_coverage*100:.2f}%")
        
        optimization_time = time.time() - start_time
        achieved_target = current_coverage >= target_coverage
        coverage_gain = current_coverage - original_coverage
        cost_effectiveness = coverage_gain / total_cost if total_cost > 0 else 0
        
        print(f"\n混合增补优化完成!")
        print(f"最终覆盖率: {current_coverage*100:.2f}%")
        print(f"增补成本: {total_cost:.1f}")
        print(f"新增卫星: {len(added_satellites)} 个")
        print(f"新增地面传感器: {len(added_ground_sensors)} 个")
        print(f"达到目标: {'是' if achieved_target else '否'}")
        print(f"成本效益: {cost_effectiveness:.4f}")
        
        return HybridAdditionSolution(
            original_satellites=satellites,
            original_ground_sensors=ground_sensors,
            added_satellites=added_satellites,
            added_ground_sensors=added_ground_sensors,
            final_satellites=current_satellites,
            final_ground_sensors=current_ground_sensors,
            original_coverage=original_coverage,
            final_coverage=current_coverage,
            target_coverage=target_coverage,
            total_added_cost=total_cost,
            optimization_time=optimization_time,
            achieved_target=achieved_target,
            cost_effectiveness_ratio=cost_effectiveness
        )
    
    def _create_no_addition_solution(self, satellites, ground_sensors, target_coverage, start_time):
        """创建无增补的解决方案"""
        original_coverage, _ = self.evaluate_deployment(satellites, ground_sensors)
        
        return HybridAdditionSolution(
            original_satellites=satellites,
            original_ground_sensors=ground_sensors,
            added_satellites=[],
            added_ground_sensors=[],
            final_satellites=satellites,
            final_ground_sensors=ground_sensors,
            original_coverage=original_coverage,
            final_coverage=original_coverage,
            target_coverage=target_coverage,
            total_added_cost=0,
            optimization_time=time.time() - start_time,
            achieved_target=original_coverage >= target_coverage,
            cost_effectiveness_ratio=0
        )
    
    def visualize_addition_result(self, solution: HybridAdditionSolution, 
                                title: str = "混合传感器增补优化结果"):
        """可视化增补结果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 绘制原始方案
        self._plot_deployment(ax1, solution.original_satellites, 
                             solution.original_ground_sensors, [],
                             [], f"原始方案 (覆盖率: {solution.original_coverage*100:.1f}%)")
        
        # 绘制增补方案
        self._plot_deployment(ax2, solution.original_satellites, 
                             solution.original_ground_sensors,
                             solution.added_satellites, solution.added_ground_sensors,
                             f"增补方案 (覆盖率: {solution.final_coverage*100:.1f}%)")
        
        plt.suptitle(f"{title}\n"
                    f"目标: {solution.target_coverage*100:.1f}% | "
                    f"增补成本: {solution.total_added_cost:.1f} | "
                    f"新增: 卫星{len(solution.added_satellites)}个+地面{len(solution.added_ground_sensors)}个 | "
                    f"达到目标: {'是' if solution.achieved_target else '否'}", fontsize=14)
        plt.tight_layout()
        plt.show()
    
    def _plot_deployment(self, ax, original_satellites, original_ground_sensors,
                        added_satellites, added_ground_sensors, title):
        """绘制部署方案"""
        # 绘制目标区域
        x_coords, y_coords = self.target_area.exterior.xy
        ax.plot(x_coords, y_coords, 'b-', linewidth=2, label='目标区域')
        ax.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
        
        # 绘制原有卫星
        for i, sat in enumerate(original_satellites):
            coverage = sat.get_coverage_area()
            if coverage and not coverage.is_empty:
                x_coords, y_coords = coverage.exterior.xy
                ax.plot(x_coords, y_coords, 'r-', alpha=0.6, linewidth=1)
                ax.fill(x_coords, y_coords, alpha=0.15, color='red')
                
                ax.plot([sat.start_x, sat.end_x], [sat.start_y, sat.end_y], 
                       'r-', linewidth=2, alpha=0.8)
                ax.text((sat.start_x + sat.end_x)/2, (sat.start_y + sat.end_y)/2, 
                       f'S{i+1}', fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='red', alpha=0.7))
        
        # 绘制新增卫星
        for i, sat in enumerate(added_satellites):
            coverage = sat.get_coverage_area()
            if coverage and not coverage.is_empty:
                x_coords, y_coords = coverage.exterior.xy
                ax.plot(x_coords, y_coords, 'orange', alpha=0.8, linewidth=2)
                ax.fill(x_coords, y_coords, alpha=0.25, color='orange')
                
                ax.plot([sat.start_x, sat.end_x], [sat.start_y, sat.end_y], 
                       'orange', linewidth=3, alpha=1.0)
                ax.text((sat.start_x + sat.end_x)/2, (sat.start_y + sat.end_y)/2, 
                       f'NS{i+1}', fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='orange', alpha=0.8))
        
        # 绘制原有地面传感器
        for i, sensor in enumerate(original_ground_sensors):
            circle = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                              fill=False, color='green', alpha=0.6, linewidth=1)
            ax.add_patch(circle)
            circle_fill = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                                   fill=True, color='green', alpha=0.15)
            ax.add_patch(circle_fill)
            
            ax.plot(sensor.x, sensor.y, 'go', markersize=6)
            ax.text(sensor.x, sensor.y + sensor.radius + 0.2, f'G{i+1}', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='green', alpha=0.7))
        
        # 绘制新增地面传感器
        for i, sensor in enumerate(added_ground_sensors):
            circle = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                              fill=False, color='purple', alpha=0.8, linewidth=2)
            ax.add_patch(circle)
            circle_fill = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                                   fill=True, color='purple', alpha=0.25)
            ax.add_patch(circle_fill)
            
            ax.plot(sensor.x, sensor.y, 'o', color='purple', markersize=8)
            ax.text(sensor.x, sensor.y + sensor.radius + 0.2, f'NG{i+1}', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='purple', alpha=0.8))
        
        ax.set_xlabel('X 坐标')
        ax.set_ylabel('Y 坐标')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # 设置坐标轴范围
        minx, miny, maxx, maxy = self.target_area.bounds
        margin = (maxx - minx) * 0.1
        ax.set_xlim(minx - margin, maxx + margin)
        ax.set_ylim(miny - margin, maxy + margin)


def demo_hybrid_sensor_addition_optimize():
    """演示混合传感器增补优化"""
    print("="*60)
    print("混合传感器增补优化演示（最少增补传感器）")
    print("="*60)
    
    # 创建目标区域
    target_area = Polygon([(0, 0), (18, 0), (18, 15), (0, 15)])
    
    # 创建一个覆盖不足的现有部署方案
    existing_satellites = [
        Satellite(0, start_x=3, start_y=0, end_x=5, end_y=15, swath_width=2.5, cost=80),
    ]
    
    existing_ground_sensors = [
        GroundSensor(0, 8, 3, 2.0, cost=10),
        GroundSensor(1, 12, 8, 2.0, cost=12),
        GroundSensor(2, 15, 12, 2.0, cost=11),
    ]
    
    target_coverage = 0.85  # 目标85%覆盖率
    max_budget = 200
    
    print(f"现有部署方案:")
    print(f"- 卫星: {len(existing_satellites)} 个")
    print(f"- 地面传感器: {len(existing_ground_sensors)} 个")
    print(f"- 目标覆盖率: {target_coverage*100}%")
    print(f"- 增补预算: {max_budget}")
    
    # 创建优化器
    optimizer = HybridSensorAdditionOptimizer(target_area, grid_resolution=0.4)
    
    # 评估原始方案
    original_coverage, _ = optimizer.evaluate_deployment(existing_satellites, existing_ground_sensors)
    print(f"- 原始覆盖率: {original_coverage*100:.2f}%")
    
    # 进行增补优化
    solution = optimizer.optimize_additions_greedy(
        existing_satellites, existing_ground_sensors,
        target_coverage, max_budget, max_additions=8
    )
    
    # 显示优化结果
    print(f"\n混合增补优化结果:")
    print(f"最终覆盖率: {solution.final_coverage*100:.2f}%")
    print(f"新增卫星: {len(solution.added_satellites)} 个")
    print(f"新增地面传感器: {len(solution.added_ground_sensors)} 个")
    print(f"总增补成本: {solution.total_added_cost:.1f}")
    print(f"是否达到目标: {solution.achieved_target}")
    print(f"成本效益比: {solution.cost_effectiveness_ratio:.4f}")
    
    # 详细分析
    if solution.added_satellites:
        print(f"\n新增卫星详情:")
        for i, sat in enumerate(solution.added_satellites):
            print(f"  卫星 {i+1}: 轨道({sat.start_x:.1f},{sat.start_y:.1f})-({sat.end_x:.1f},{sat.end_y:.1f}), "
                  f"宽度: {sat.swath_width:.1f}, 成本: {sat.cost:.1f}")
    
    if solution.added_ground_sensors:
        print(f"\n新增地面传感器详情:")
        for i, sensor in enumerate(solution.added_ground_sensors):
            print(f"  传感器 {i+1}: 位置({sensor.x:.1f},{sensor.y:.1f}), "
                  f"半径: {sensor.radius:.1f}, 成本: {sensor.cost:.1f}")
    
    # 可视化结果
    optimizer.visualize_addition_result(solution)
    
    return optimizer, solution


if __name__ == "__main__":
    demo_hybrid_sensor_addition_optimize()