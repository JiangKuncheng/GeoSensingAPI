"""
空间-地面传感器网络启发式优化算法
包含遗传算法(GA)和模拟退火(SA)算法，用于解决大规模传感器选址问题

主要功能：
1. 卫星和地面传感器混合选择优化
2. 资源约束下的覆盖最大化
3. 动态移动传感器调整
4. 多目标优化（覆盖率 vs 成本）

作者：GeoSensingAPI
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import random
import math
import time
from typing import List, Tuple, Dict, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
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
    swath_width: float  # 条带宽度
    cost: float = 100.0
    bandwidth: float = 50.0
    max_roll_count: int = 3
    orbit_direction: float = 0.0  # 轨道方向角度（弧度）
    
    def get_coverage_polygon(self) -> Polygon:
        """获取卫星覆盖区域的多边形（条带状）"""
        # 计算条带方向向量
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        length = math.sqrt(dx**2 + dy**2)
        
        if length == 0:
            # 如果起点终点相同，创建一个小的正方形区域
            half_width = self.swath_width / 2
            return Polygon([
                (self.start_x - half_width, self.start_y - half_width),
                (self.start_x + half_width, self.start_y - half_width),
                (self.start_x + half_width, self.start_y + half_width),
                (self.start_x - half_width, self.start_y + half_width)
            ])
        
        # 单位方向向量
        unit_dx = dx / length
        unit_dy = dy / length
        
        # 垂直方向向量（用于条带宽度）
        perp_dx = -unit_dy * self.swath_width / 2
        perp_dy = unit_dx * self.swath_width / 2
        
        # 构建条带多边形的四个顶点
        vertices = [
            (self.start_x + perp_dx, self.start_y + perp_dy),  # 起点左侧
            (self.start_x - perp_dx, self.start_y - perp_dy),  # 起点右侧
            (self.end_x - perp_dx, self.end_y - perp_dy),      # 终点右侧
            (self.end_x + perp_dx, self.end_y + perp_dy)       # 终点左侧
        ]
        
        return Polygon(vertices)
    
    def can_cover_point(self, x: float, y: float) -> bool:
        """检查点是否在卫星覆盖范围内"""
        return self.get_coverage_polygon().contains(Point(x, y))
    
    @property
    def center_x(self) -> float:
        """条带中心点X坐标（用于向后兼容）"""
        return (self.start_x + self.end_x) / 2
    
    @property
    def center_y(self) -> float:
        """条带中心点Y坐标（用于向后兼容）"""
        return (self.start_y + self.end_y) / 2
    
    @property
    def length(self) -> float:
        """条带长度"""
        return math.sqrt((self.end_x - self.start_x)**2 + (self.end_y - self.start_y)**2)

@dataclass
class GroundSensor:
    """地面传感器类"""
    id: int
    x: float
    y: float
    radius: float
    cost: float = 10.0
    bandwidth: float = 20.0
    mobile: bool = False
    move_range: float = 0.0
    
    def get_coverage_polygon(self) -> Polygon:
        """获取地面传感器覆盖区域的多边形（圆形）"""
        return Point(self.x, self.y).buffer(self.radius)
    
    def can_cover_point(self, x: float, y: float) -> bool:
        """检查点是否在传感器覆盖范围内"""
        distance = math.sqrt((x - self.x)**2 + (y - self.y)**2)
        return distance <= self.radius
    
    def move_to(self, new_x: float, new_y: float) -> bool:
        """移动传感器到新位置（如果在移动范围内）"""
        if not self.mobile:
            return False
        
        original_x, original_y = self.x, self.y
        distance = math.sqrt((new_x - original_x)**2 + (new_y - original_y)**2)
        
        if distance <= self.move_range:
            self.x, self.y = new_x, new_y
            return True
        return False

@dataclass
class ResourceConstraints:
    """资源约束条件"""
    max_satellites: int = 10
    max_ground_sensors: int = 20
    max_total_cost: float = 1000.0
    max_bandwidth: float = 500.0
    target_coverage_ratio: float = 0.9
    
class SensorSelectionSolution:
    """传感器选择方案"""
    def __init__(self):
        self.selected_satellites: List[int] = []
        self.selected_ground_sensors: List[int] = []
        self.fitness: float = 0.0
        self.coverage_ratio: float = 0.0
        self.total_cost: float = 0.0
        self.total_bandwidth: float = 0.0
        self.penalty: float = 0.0
    
    def copy(self):
        """创建解的副本"""
        new_solution = SensorSelectionSolution()
        new_solution.selected_satellites = self.selected_satellites.copy()
        new_solution.selected_ground_sensors = self.selected_ground_sensors.copy()
        new_solution.fitness = self.fitness
        new_solution.coverage_ratio = self.coverage_ratio
        new_solution.total_cost = self.total_cost
        new_solution.total_bandwidth = self.total_bandwidth
        new_solution.penalty = self.penalty
        return new_solution

class SensorNetworkOptimizer:
    """传感器网络优化器基类"""
    
    def __init__(self, target_area: Polygon, satellites: List[Satellite], 
                 ground_sensors: List[GroundSensor], constraints: ResourceConstraints,
                 grid_resolution: float = 0.5):
        self.target_area = target_area
        self.satellites = satellites
        self.ground_sensors = ground_sensors
        self.constraints = constraints
        self.grid_resolution = grid_resolution
        
        # 生成目标区域网格点用于覆盖计算
        self._generate_grid_points()
        
    def _generate_grid_points(self):
        """生成目标区域的网格点"""
        minx, miny, maxx, maxy = self.target_area.bounds
        x_coords = np.arange(minx, maxx + self.grid_resolution, self.grid_resolution)
        y_coords = np.arange(miny, maxy + self.grid_resolution, self.grid_resolution)
        
        self.grid_points = []
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point) or self.target_area.touches(point):
                    self.grid_points.append((x, y))
        
        print(f"目标区域网格点数量: {len(self.grid_points)}")
    
    def calculate_coverage_ratio(self, solution: SensorSelectionSolution) -> float:
        """计算解的覆盖率"""
        if not solution.selected_satellites and not solution.selected_ground_sensors:
            return 0.0
        
        covered_points = set()
        
        # 计算卫星覆盖
        for sat_id in solution.selected_satellites:
            satellite = self.satellites[sat_id]
            for i, (x, y) in enumerate(self.grid_points):
                if satellite.can_cover_point(x, y):
                    covered_points.add(i)
        
        # 计算地面传感器覆盖
        for sensor_id in solution.selected_ground_sensors:
            sensor = self.ground_sensors[sensor_id]
            for i, (x, y) in enumerate(self.grid_points):
                if sensor.can_cover_point(x, y):
                    covered_points.add(i)
        
        coverage_ratio = len(covered_points) / len(self.grid_points)
        return coverage_ratio
    
    def calculate_total_cost(self, solution: SensorSelectionSolution) -> float:
        """计算解的总成本"""
        total_cost = 0.0
        
        for sat_id in solution.selected_satellites:
            total_cost += self.satellites[sat_id].cost
        
        for sensor_id in solution.selected_ground_sensors:
            total_cost += self.ground_sensors[sensor_id].cost
        
        return total_cost
    
    def calculate_total_bandwidth(self, solution: SensorSelectionSolution) -> float:
        """计算解的总带宽需求"""
        total_bandwidth = 0.0
        
        for sat_id in solution.selected_satellites:
            total_bandwidth += self.satellites[sat_id].bandwidth
        
        for sensor_id in solution.selected_ground_sensors:
            total_bandwidth += self.ground_sensors[sensor_id].bandwidth
        
        return total_bandwidth
    
    def evaluate_solution(self, solution: SensorSelectionSolution) -> float:
        """评估解的适应度"""
        solution.coverage_ratio = self.calculate_coverage_ratio(solution)
        solution.total_cost = self.calculate_total_cost(solution)
        solution.total_bandwidth = self.calculate_total_bandwidth(solution)
        
        # 计算约束违反惩罚
        penalty = 0.0
        
        # 传感器数量约束
        if len(solution.selected_satellites) > self.constraints.max_satellites:
            penalty += (len(solution.selected_satellites) - self.constraints.max_satellites) * 50
        
        if len(solution.selected_ground_sensors) > self.constraints.max_ground_sensors:
            penalty += (len(solution.selected_ground_sensors) - self.constraints.max_ground_sensors) * 10
        
        # 成本约束
        if solution.total_cost > self.constraints.max_total_cost:
            penalty += (solution.total_cost - self.constraints.max_total_cost) * 2
        
        # 带宽约束
        if solution.total_bandwidth > self.constraints.max_bandwidth:
            penalty += (solution.total_bandwidth - self.constraints.max_bandwidth) * 1
        
        solution.penalty = penalty
        
        # 适应度计算：覆盖率为主要目标，成本为次要目标
        if solution.coverage_ratio >= self.constraints.target_coverage_ratio:
            # 达到目标覆盖率，优化成本
            fitness = 1000 + solution.coverage_ratio * 500 - solution.total_cost * 0.1 - penalty
        else:
            # 未达到目标覆盖率，主要优化覆盖率
            fitness = solution.coverage_ratio * 1000 - penalty
        
        solution.fitness = fitness
        return fitness
    
    def visualize_solution(self, solution: SensorSelectionSolution, title: str = "传感器网络配置"):
        """可视化解决方案"""
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # 绘制目标区域
        if self.target_area.geom_type == 'Polygon':
            x, y = self.target_area.exterior.xy
            ax.plot(x, y, 'b-', linewidth=2, label='目标区域边界')
            ax.fill(x, y, alpha=0.2, color='lightblue', label='目标区域')
        
        # 绘制选中的卫星覆盖区域（条带状）
        for sat_id in solution.selected_satellites:
            satellite = self.satellites[sat_id]
            
            # 获取条带多边形
            swath_polygon = satellite.get_coverage_polygon()
            
            # 绘制条带覆盖区域
            if swath_polygon.geom_type == 'Polygon':
                x_coords, y_coords = swath_polygon.exterior.xy
                swath_patch = patches.Polygon(
                    list(zip(x_coords, y_coords)),
                    linewidth=2, edgecolor='red', facecolor='red', alpha=0.3
                )
                ax.add_patch(swath_patch)
            
            # 绘制卫星轨道线
            ax.plot([satellite.start_x, satellite.end_x], 
                   [satellite.start_y, satellite.end_y], 
                   'r-', linewidth=3, alpha=0.8, label='卫星轨道' if sat_id == solution.selected_satellites[0] else "")
            
            # 标注卫星起点和终点
            ax.scatter(satellite.start_x, satellite.start_y, c='red', s=80, 
                      marker='o', edgecolors='black', linewidth=1, zorder=5)
            ax.scatter(satellite.end_x, satellite.end_y, c='red', s=80, 
                      marker='s', edgecolors='black', linewidth=1, zorder=5)
            
            # 标注卫星ID
            ax.annotate(f'S{satellite.id}', 
                       (satellite.center_x, satellite.center_y), 
                       xytext=(5, 5), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7))
        
        # 绘制选中的地面传感器覆盖区域
        for sensor_id in solution.selected_ground_sensors:
            sensor = self.ground_sensors[sensor_id]
            circle = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                              fill=True, color='green', alpha=0.3)
            ax.add_patch(circle)
            
            circle_outline = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                                      fill=False, color='green', linewidth=2)
            ax.add_patch(circle_outline)
            
            # 标注传感器
            ax.scatter(sensor.x, sensor.y, c='green', s=80, 
                      marker='o', edgecolors='black', linewidth=1, zorder=5)
            ax.annotate(f'G{sensor.id}', 
                       (sensor.x, sensor.y), 
                       xytext=(5, 5), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.7))
        
        # 设置图形属性
        ax.set_xlabel('X 坐标', fontsize=12)
        ax.set_ylabel('Y 坐标', fontsize=12)
        ax.set_title(f'{title}\n'
                    f'覆盖率: {solution.coverage_ratio*100:.1f}%, '
                    f'卫星: {len(solution.selected_satellites)}, '
                    f'地面站: {len(solution.selected_ground_sensors)}, '
                    f'成本: {solution.total_cost:.1f}', 
                    fontsize=14, fontweight='bold')
        
        # 添加图例
        satellite_patch = patches.Patch(color='red', alpha=0.3, label=f'卫星覆盖 ({len(solution.selected_satellites)}个)')
        sensor_patch = patches.Patch(color='green', alpha=0.3, label=f'地面传感器覆盖 ({len(solution.selected_ground_sensors)}个)')
        ax.legend(handles=[satellite_patch, sensor_patch], loc='upper right')
        
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # 调整坐标轴范围
        minx, miny, maxx, maxy = self.target_area.bounds
        margin = 2.0
        ax.set_xlim(minx - margin, maxx + margin)
        ax.set_ylim(miny - margin, maxy + margin)
        
        plt.tight_layout()
        plt.show()

class GeneticAlgorithmOptimizer(SensorNetworkOptimizer):
    """遗传算法优化器"""
    
    def __init__(self, target_area: Polygon, satellites: List[Satellite], 
                 ground_sensors: List[GroundSensor], constraints: ResourceConstraints,
                 population_size: int = 50, generations: int = 100,
                 crossover_rate: float = 0.8, mutation_rate: float = 0.1,
                 grid_resolution: float = 0.5):
        super().__init__(target_area, satellites, ground_sensors, constraints, grid_resolution)
        self.population_size = population_size
        self.generations = generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.population = []
        self.best_solution = None
        self.fitness_history = []
    
    def initialize_population(self):
        """初始化种群"""
        self.population = []
        for _ in range(self.population_size):
            solution = SensorSelectionSolution()
            
            # 随机选择卫星（选择概率与覆盖能力相关）
            num_satellites = random.randint(0, min(len(self.satellites), self.constraints.max_satellites))
            solution.selected_satellites = random.sample(range(len(self.satellites)), num_satellites)
            
            # 随机选择地面传感器
            num_ground_sensors = random.randint(0, min(len(self.ground_sensors), self.constraints.max_ground_sensors))
            solution.selected_ground_sensors = random.sample(range(len(self.ground_sensors)), num_ground_sensors)
            
            self.evaluate_solution(solution)
            self.population.append(solution)
        
        # 更新最佳解
        self.best_solution = max(self.population, key=lambda x: x.fitness).copy()
        print(f"初始种群最佳适应度: {self.best_solution.fitness:.2f}, 覆盖率: {self.best_solution.coverage_ratio*100:.1f}%")
    
    def tournament_selection(self, tournament_size: int = 3) -> SensorSelectionSolution:
        """锦标赛选择"""
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x.fitness)
    
    def crossover(self, parent1: SensorSelectionSolution, parent2: SensorSelectionSolution) -> Tuple[SensorSelectionSolution, SensorSelectionSolution]:
        """交叉操作"""
        child1, child2 = SensorSelectionSolution(), SensorSelectionSolution()
        
        # 卫星交叉
        all_satellites = list(set(parent1.selected_satellites + parent2.selected_satellites))
        if all_satellites:
            split_point = random.randint(0, len(all_satellites))
            child1.selected_satellites = all_satellites[:split_point]
            child2.selected_satellites = all_satellites[split_point:]
        
        # 地面传感器交叉
        all_ground_sensors = list(set(parent1.selected_ground_sensors + parent2.selected_ground_sensors))
        if all_ground_sensors:
            split_point = random.randint(0, len(all_ground_sensors))
            child1.selected_ground_sensors = all_ground_sensors[:split_point]
            child2.selected_ground_sensors = all_ground_sensors[split_point:]
        
        return child1, child2
    
    def mutate(self, solution: SensorSelectionSolution):
        """变异操作"""
        # 卫星变异
        if random.random() < self.mutation_rate:
            if solution.selected_satellites and random.random() < 0.5:
                # 移除一个卫星
                solution.selected_satellites.remove(random.choice(solution.selected_satellites))
            else:
                # 添加一个卫星
                available = [i for i in range(len(self.satellites)) if i not in solution.selected_satellites]
                if available and len(solution.selected_satellites) < self.constraints.max_satellites:
                    solution.selected_satellites.append(random.choice(available))
        
        # 地面传感器变异
        if random.random() < self.mutation_rate:
            if solution.selected_ground_sensors and random.random() < 0.5:
                # 移除一个传感器
                solution.selected_ground_sensors.remove(random.choice(solution.selected_ground_sensors))
            else:
                # 添加一个传感器
                available = [i for i in range(len(self.ground_sensors)) if i not in solution.selected_ground_sensors]
                if available and len(solution.selected_ground_sensors) < self.constraints.max_ground_sensors:
                    solution.selected_ground_sensors.append(random.choice(available))
    
    def optimize(self) -> SensorSelectionSolution:
        """执行遗传算法优化"""
        print("开始遗传算法优化...")
        start_time = time.time()
        
        self.initialize_population()
        
        for generation in range(self.generations):
            new_population = []
            
            # 精英保留
            elite_size = max(1, self.population_size // 10)
            elite = sorted(self.population, key=lambda x: x.fitness, reverse=True)[:elite_size]
            new_population.extend([sol.copy() for sol in elite])
            
            # 生成新个体
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection()
                parent2 = self.tournament_selection()
                
                if random.random() < self.crossover_rate:
                    child1, child2 = self.crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                self.mutate(child1)
                self.mutate(child2)
                
                self.evaluate_solution(child1)
                self.evaluate_solution(child2)
                
                new_population.extend([child1, child2])
            
            # 更新种群
            self.population = new_population[:self.population_size]
            
            # 更新最佳解
            current_best = max(self.population, key=lambda x: x.fitness)
            if current_best.fitness > self.best_solution.fitness:
                self.best_solution = current_best.copy()
            
            # 记录历史
            avg_fitness = sum(sol.fitness for sol in self.population) / len(self.population)
            self.fitness_history.append({
                'generation': generation,
                'best_fitness': self.best_solution.fitness,
                'avg_fitness': avg_fitness,
                'best_coverage': self.best_solution.coverage_ratio
            })
            
            if generation % 10 == 0:
                print(f"第 {generation} 代: 最佳适应度={self.best_solution.fitness:.2f}, "
                      f"覆盖率={self.best_solution.coverage_ratio*100:.1f}%, "
                      f"成本={self.best_solution.total_cost:.1f}")
        
        end_time = time.time()
        print(f"遗传算法优化完成，耗时: {end_time - start_time:.2f} 秒")
        print(f"最终结果: 覆盖率={self.best_solution.coverage_ratio*100:.2f}%, "
              f"卫星数量={len(self.best_solution.selected_satellites)}, "
              f"地面传感器数量={len(self.best_solution.selected_ground_sensors)}, "
              f"总成本={self.best_solution.total_cost:.1f}")
        
        return self.best_solution

class SimulatedAnnealingOptimizer(SensorNetworkOptimizer):
    """模拟退火算法优化器"""
    
    def __init__(self, target_area: Polygon, satellites: List[Satellite], 
                 ground_sensors: List[GroundSensor], constraints: ResourceConstraints,
                 initial_temperature: float = 1000.0, final_temperature: float = 1.0,
                 cooling_rate: float = 0.95, max_iterations: int = 1000,
                 grid_resolution: float = 0.5):
        super().__init__(target_area, satellites, ground_sensors, constraints, grid_resolution)
        self.initial_temperature = initial_temperature
        self.final_temperature = final_temperature
        self.cooling_rate = cooling_rate
        self.max_iterations = max_iterations
        self.current_solution = None
        self.best_solution = None
        self.temperature_history = []
    
    def generate_initial_solution(self) -> SensorSelectionSolution:
        """生成初始解"""
        solution = SensorSelectionSolution()
        
        # 贪心初始化：优先选择覆盖能力强的传感器
        satellite_coverage_scores = []
        for i, sat in enumerate(self.satellites):
            coverage_area = sat.width * sat.height
            efficiency = coverage_area / sat.cost
            satellite_coverage_scores.append((i, efficiency))
        
        ground_sensor_coverage_scores = []
        for i, sensor in enumerate(self.ground_sensors):
            coverage_area = math.pi * sensor.radius ** 2
            efficiency = coverage_area / sensor.cost
            ground_sensor_coverage_scores.append((i, efficiency))
        
        # 按效率排序并选择前几个
        satellite_coverage_scores.sort(key=lambda x: x[1], reverse=True)
        ground_sensor_coverage_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 选择部分高效率的传感器
        num_satellites = min(len(self.satellites) // 2, self.constraints.max_satellites)
        num_ground_sensors = min(len(self.ground_sensors) // 2, self.constraints.max_ground_sensors)
        
        solution.selected_satellites = [sat_id for sat_id, _ in satellite_coverage_scores[:num_satellites]]
        solution.selected_ground_sensors = [sensor_id for sensor_id, _ in ground_sensor_coverage_scores[:num_ground_sensors]]
        
        self.evaluate_solution(solution)
        return solution
    
    def generate_neighbor(self, solution: SensorSelectionSolution) -> SensorSelectionSolution:
        """生成邻域解"""
        neighbor = solution.copy()
        
        # 随机选择变化类型
        change_type = random.choice(['add_satellite', 'remove_satellite', 'add_ground', 'remove_ground'])
        
        if change_type == 'add_satellite':
            available = [i for i in range(len(self.satellites)) if i not in neighbor.selected_satellites]
            if available and len(neighbor.selected_satellites) < self.constraints.max_satellites:
                neighbor.selected_satellites.append(random.choice(available))
        
        elif change_type == 'remove_satellite':
            if neighbor.selected_satellites:
                neighbor.selected_satellites.remove(random.choice(neighbor.selected_satellites))
        
        elif change_type == 'add_ground':
            available = [i for i in range(len(self.ground_sensors)) if i not in neighbor.selected_ground_sensors]
            if available and len(neighbor.selected_ground_sensors) < self.constraints.max_ground_sensors:
                neighbor.selected_ground_sensors.append(random.choice(available))
        
        elif change_type == 'remove_ground':
            if neighbor.selected_ground_sensors:
                neighbor.selected_ground_sensors.remove(random.choice(neighbor.selected_ground_sensors))
        
        self.evaluate_solution(neighbor)
        return neighbor
    
    def accept_probability(self, current_fitness: float, new_fitness: float, temperature: float) -> float:
        """计算接受概率"""
        if new_fitness > current_fitness:
            return 1.0
        else:
            return math.exp((new_fitness - current_fitness) / temperature)
    
    def optimize(self) -> SensorSelectionSolution:
        """执行模拟退火优化"""
        print("开始模拟退火优化...")
        start_time = time.time()
        
        # 初始化
        self.current_solution = self.generate_initial_solution()
        self.best_solution = self.current_solution.copy()
        
        temperature = self.initial_temperature
        iteration = 0
        
        print(f"初始解: 覆盖率={self.current_solution.coverage_ratio*100:.1f}%, "
              f"成本={self.current_solution.total_cost:.1f}")
        
        while temperature > self.final_temperature and iteration < self.max_iterations:
            # 生成邻域解
            neighbor = self.generate_neighbor(self.current_solution)
            
            # 计算适应度差
            delta_fitness = neighbor.fitness - self.current_solution.fitness
            
            # 决定是否接受新解
            if delta_fitness > 0 or random.random() < self.accept_probability(
                self.current_solution.fitness, neighbor.fitness, temperature):
                self.current_solution = neighbor
                
                # 更新最佳解
                if self.current_solution.fitness > self.best_solution.fitness:
                    self.best_solution = self.current_solution.copy()
            
            # 记录历史
            self.temperature_history.append({
                'iteration': iteration,
                'temperature': temperature,
                'current_fitness': self.current_solution.fitness,
                'best_fitness': self.best_solution.fitness,
                'current_coverage': self.current_solution.coverage_ratio,
                'best_coverage': self.best_solution.coverage_ratio
            })
            
            # 降温
            temperature *= self.cooling_rate
            iteration += 1
            
            if iteration % 100 == 0:
                print(f"迭代 {iteration}: 温度={temperature:.2f}, "
                      f"当前适应度={self.current_solution.fitness:.2f}, "
                      f"最佳覆盖率={self.best_solution.coverage_ratio*100:.1f}%")
        
        end_time = time.time()
        print(f"模拟退火优化完成，耗时: {end_time - start_time:.2f} 秒")
        print(f"最终结果: 覆盖率={self.best_solution.coverage_ratio*100:.2f}%, "
              f"卫星数量={len(self.best_solution.selected_satellites)}, "
              f"地面传感器数量={len(self.best_solution.selected_ground_sensors)}, "
              f"总成本={self.best_solution.total_cost:.1f}")
        
        return self.best_solution

class ResourceBalanceOptimizer:
    """资源平衡优化器"""
    
    def __init__(self, optimizer: SensorNetworkOptimizer):
        self.optimizer = optimizer
        self.pareto_solutions = []
    
    def multi_objective_optimization(self, budget_levels: List[float]) -> List[SensorSelectionSolution]:
        """多目标优化：寻找成本-覆盖率帕累托前沿"""
        print("开始多目标资源平衡优化...")
        
        self.pareto_solutions = []
        
        for budget in budget_levels:
            print(f"\n--- 预算约束: {budget} ---")
            
            # 更新约束条件
            original_max_cost = self.optimizer.constraints.max_total_cost
            self.optimizer.constraints.max_total_cost = budget
            
            # 运行优化
            if isinstance(self.optimizer, GeneticAlgorithmOptimizer):
                solution = self.optimizer.optimize()
            elif isinstance(self.optimizer, SimulatedAnnealingOptimizer):
                solution = self.optimizer.optimize()
            else:
                raise ValueError("不支持的优化器类型")
            
            if solution.total_cost <= budget:
                self.pareto_solutions.append(solution.copy())
                print(f"预算 {budget}: 覆盖率={solution.coverage_ratio*100:.1f}%, "
                      f"实际成本={solution.total_cost:.1f}")
            else:
                print(f"预算 {budget}: 无法找到满足约束的解")
            
            # 恢复原始约束
            self.optimizer.constraints.max_total_cost = original_max_cost
        
        return self.pareto_solutions
    
    def analyze_marginal_efficiency(self) -> Dict:
        """分析边际效率"""
        if len(self.pareto_solutions) < 2:
            return {"error": "需要至少2个解进行边际分析"}
        
        # 按成本排序
        sorted_solutions = sorted(self.pareto_solutions, key=lambda x: x.total_cost)
        
        marginal_analysis = []
        for i in range(1, len(sorted_solutions)):
            prev_sol = sorted_solutions[i-1]
            curr_sol = sorted_solutions[i]
            
            cost_increase = curr_sol.total_cost - prev_sol.total_cost
            coverage_increase = curr_sol.coverage_ratio - prev_sol.coverage_ratio
            
            efficiency = coverage_increase / cost_increase if cost_increase > 0 else 0
            
            marginal_analysis.append({
                'cost_range': f"{prev_sol.total_cost:.1f} → {curr_sol.total_cost:.1f}",
                'coverage_increase': coverage_increase * 100,
                'cost_increase': cost_increase,
                'marginal_efficiency': efficiency
            })
        
        return {
            'marginal_analysis': marginal_analysis,
            'best_efficiency_range': max(marginal_analysis, key=lambda x: x['marginal_efficiency']) if marginal_analysis else None
        }
    
    def visualize_pareto_front(self):
        """可视化帕累托前沿"""
        if not self.pareto_solutions:
            print("没有帕累托解可视化")
            return
        
        costs = [sol.total_cost for sol in self.pareto_solutions]
        coverages = [sol.coverage_ratio * 100 for sol in self.pareto_solutions]
        
        plt.figure(figsize=(10, 6))
        plt.scatter(costs, coverages, c='red', s=100, alpha=0.7, edgecolors='black')
        plt.plot(costs, coverages, 'r--', alpha=0.5)
        
        # 标注每个点
        for i, (cost, coverage) in enumerate(zip(costs, coverages)):
            plt.annotate(f'解{i+1}', (cost, coverage), xytext=(5, 5), 
                        textcoords='offset points', fontsize=9)
        
        plt.xlabel('总成本')
        plt.ylabel('覆盖率 (%)')
        plt.title('成本-覆盖率帕累托前沿', fontweight='bold')
        plt.grid(True, alpha=0.3)
        
        # 添加目标覆盖率线
        target_coverage = self.optimizer.constraints.target_coverage_ratio * 100
        plt.axhline(y=target_coverage, color='green', linestyle='--', 
                   label=f'目标覆盖率 {target_coverage}%', alpha=0.7)
        plt.legend()
        
        plt.tight_layout()
        plt.show()

class DynamicSensorAdjuster:
    """动态传感器调整器"""
    
    def __init__(self, optimizer: SensorNetworkOptimizer, time_windows: int = 4):
        self.optimizer = optimizer
        self.time_windows = time_windows
        self.mobile_sensors = [i for i, sensor in enumerate(optimizer.ground_sensors) if sensor.mobile]
        self.adjustment_history = []
    
    def generate_time_varying_demands(self) -> List[Polygon]:
        """生成时间变化的覆盖需求区域"""
        base_area = self.optimizer.target_area
        minx, miny, maxx, maxy = base_area.bounds
        width, height = maxx - minx, maxy - miny
        
        time_demands = []
        for t in range(self.time_windows):
            # 模拟需求区域的时间变化
            shift_x = width * 0.1 * math.sin(2 * math.pi * t / self.time_windows)
            shift_y = height * 0.1 * math.cos(2 * math.pi * t / self.time_windows)
            
            # 创建偏移的需求区域
            shifted_coords = []
            if base_area.geom_type == 'Polygon':
                for x, y in base_area.exterior.coords:
                    shifted_coords.append((x + shift_x, y + shift_y))
                time_demands.append(Polygon(shifted_coords))
            else:
                time_demands.append(base_area)  # 如果不是多边形，使用原区域
        
        return time_demands
    
    def optimize_for_time_window(self, time_demand: Polygon, window_id: int) -> SensorSelectionSolution:
        """为特定时间窗口优化传感器配置"""
        print(f"\n--- 时间窗口 {window_id} 优化 ---")
        
        # 临时更新目标区域
        original_area = self.optimizer.target_area
        self.optimizer.target_area = time_demand
        self.optimizer._generate_grid_points()  # 重新生成网格点
        
        # 运行优化
        if isinstance(self.optimizer, GeneticAlgorithmOptimizer):
            # 减少遗传算法的代数以加快速度
            original_generations = self.optimizer.generations
            self.optimizer.generations = max(20, original_generations // 4)
            solution = self.optimizer.optimize()
            self.optimizer.generations = original_generations
        elif isinstance(self.optimizer, SimulatedAnnealingOptimizer):
            # 减少模拟退火的迭代次数
            original_iterations = self.optimizer.max_iterations
            self.optimizer.max_iterations = max(200, original_iterations // 4)
            solution = self.optimizer.optimize()
            self.optimizer.max_iterations = original_iterations
        else:
            raise ValueError("不支持的优化器类型")
        
        # 恢复原始目标区域
        self.optimizer.target_area = original_area
        self.optimizer._generate_grid_points()
        
        return solution
    
    def dynamic_adjustment(self) -> List[SensorSelectionSolution]:
        """执行动态调整优化"""
        print("开始动态传感器调整优化...")
        
        # 生成时间变化的需求
        time_demands = self.generate_time_varying_demands()
        
        time_solutions = []
        
        for t, demand in enumerate(time_demands):
            solution = self.optimize_for_time_window(demand, t)
            time_solutions.append(solution)
            
            self.adjustment_history.append({
                'time_window': t,
                'solution': solution.copy(),
                'coverage_ratio': solution.coverage_ratio,
                'total_cost': solution.total_cost,
                'demand_area': demand
            })
            
            print(f"时间窗口 {t}: 覆盖率={solution.coverage_ratio*100:.1f}%, "
                  f"卫星={len(solution.selected_satellites)}, "
                  f"地面站={len(solution.selected_ground_sensors)}")
        
        return time_solutions
    
    def analyze_sensor_mobility(self, time_solutions: List[SensorSelectionSolution]) -> Dict:
        """分析传感器移动性需求"""
        if len(time_solutions) < 2:
            return {"error": "需要至少2个时间窗口进行移动性分析"}
        
        mobility_analysis = {
            'satellite_changes': [],
            'ground_sensor_changes': [],
            'total_reconfigurations': 0
        }
        
        for t in range(1, len(time_solutions)):
            prev_sol = time_solutions[t-1]
            curr_sol = time_solutions[t]
            
            # 分析卫星变化
            prev_satellites = set(prev_sol.selected_satellites)
            curr_satellites = set(curr_sol.selected_satellites)
            
            added_satellites = curr_satellites - prev_satellites
            removed_satellites = prev_satellites - curr_satellites
            
            mobility_analysis['satellite_changes'].append({
                'time_window': f"{t-1} → {t}",
                'added': list(added_satellites),
                'removed': list(removed_satellites),
                'change_count': len(added_satellites) + len(removed_satellites)
            })
            
            # 分析地面传感器变化
            prev_ground = set(prev_sol.selected_ground_sensors)
            curr_ground = set(curr_sol.selected_ground_sensors)
            
            added_ground = curr_ground - prev_ground
            removed_ground = prev_ground - curr_ground
            
            mobility_analysis['ground_sensor_changes'].append({
                'time_window': f"{t-1} → {t}",
                'added': list(added_ground),
                'removed': list(removed_ground),
                'change_count': len(added_ground) + len(removed_ground)
            })
            
            mobility_analysis['total_reconfigurations'] += len(added_satellites) + len(removed_satellites) + len(added_ground) + len(removed_ground)
        
        return mobility_analysis
    
    def visualize_dynamic_coverage(self, time_solutions: List[SensorSelectionSolution]):
        """可视化动态覆盖变化"""
        if not time_solutions:
            print("没有动态解可视化")
            return
        
        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()
        
        for t, (solution, demand) in enumerate(zip(time_solutions[:4], self.adjustment_history[:4])):
            ax = axes[t]
            
            # 绘制需求区域
            if demand['demand_area'].geom_type == 'Polygon':
                x, y = demand['demand_area'].exterior.xy
                ax.plot(x, y, 'b-', linewidth=2, label='需求区域')
                ax.fill(x, y, alpha=0.2, color='lightblue')
            
            # 绘制选中的传感器
            for sat_id in solution.selected_satellites:
                satellite = self.optimizer.satellites[sat_id]
                rect = patches.Rectangle(
                    (satellite.center_x - satellite.width/2, satellite.center_y - satellite.height/2),
                    satellite.width, satellite.height,
                    linewidth=1, edgecolor='red', facecolor='red', alpha=0.3
                )
                ax.add_patch(rect)
                ax.scatter(satellite.center_x, satellite.center_y, c='red', s=50, marker='s')
            
            for sensor_id in solution.selected_ground_sensors:
                sensor = self.optimizer.ground_sensors[sensor_id]
                circle = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                                  fill=True, color='green', alpha=0.3)
                ax.add_patch(circle)
                ax.scatter(sensor.x, sensor.y, c='green', s=50)
            
            ax.set_title(f'时间窗口 {t} (覆盖率: {solution.coverage_ratio*100:.1f}%)', fontweight='bold')
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            
            # 设置坐标轴范围
            original_bounds = self.optimizer.target_area.bounds
            margin = 2.0
            ax.set_xlim(original_bounds[0] - margin, original_bounds[2] + margin)
            ax.set_ylim(original_bounds[1] - margin, original_bounds[3] + margin)
        
        plt.tight_layout()
        plt.show()
        
        # 绘制覆盖率时间序列
        plt.figure(figsize=(10, 6))
        coverages = [sol.coverage_ratio * 100 for sol in time_solutions]
        costs = [sol.total_cost for sol in time_solutions]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        ax1.plot(range(len(coverages)), coverages, 'bo-', linewidth=2, markersize=8)
        ax1.axhline(y=self.optimizer.constraints.target_coverage_ratio * 100, 
                   color='red', linestyle='--', label='目标覆盖率')
        ax1.set_ylabel('覆盖率 (%)')
        ax1.set_title('动态覆盖率变化', fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        ax2.plot(range(len(costs)), costs, 'go-', linewidth=2, markersize=8)
        ax2.set_xlabel('时间窗口')
        ax2.set_ylabel('总成本')
        ax2.set_title('动态成本变化', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()

def create_test_scenario():
    """创建测试场景"""
    # 目标区域
    target_area = Polygon([(0, 0), (20, 0), (20, 15), (0, 15)])
    
    # 创建卫星传感器（条带状覆盖）
    satellites = []
    
    # 模拟不同方向的卫星轨道
    orbit_patterns = [
        # 南北向轨道
        {"direction": "NS", "angle": 0},
        {"direction": "NS", "angle": math.pi/12},  # 轻微倾斜
        {"direction": "NS", "angle": -math.pi/12},
        
        # 东西向轨道
        {"direction": "EW", "angle": math.pi/2},
        {"direction": "EW", "angle": math.pi/2 + math.pi/15},
        
        # 斜向轨道
        {"direction": "Diag", "angle": math.pi/4},
        {"direction": "Diag", "angle": -math.pi/4},
        {"direction": "Diag", "angle": 3*math.pi/4}
    ]
    
    for i in range(8):
        pattern = orbit_patterns[i % len(orbit_patterns)]
        
        if pattern["direction"] == "NS":  # 南北向
            start_x = random.uniform(2, 18)
            start_y = 0
            end_x = start_x + 5 * math.sin(pattern["angle"])
            end_y = 15
        elif pattern["direction"] == "EW":  # 东西向
            start_x = 0
            start_y = random.uniform(2, 13)
            end_x = 20
            end_y = start_y + 3 * math.sin(pattern["angle"] - math.pi/2)
        else:  # 斜向
            if pattern["angle"] > 0:  # 正斜率
                start_x = random.uniform(0, 5)
                start_y = 0
                end_x = start_x + 15
                end_y = 15
            else:  # 负斜率
                start_x = random.uniform(15, 20)
                start_y = 0
                end_x = start_x - 15
                end_y = 15
        
        # 确保轨道在目标区域内
        start_x = max(0, min(20, start_x))
        start_y = max(0, min(15, start_y))
        end_x = max(0, min(20, end_x))
        end_y = max(0, min(15, end_y))
        
        swath_width = random.uniform(2, 4)  # 条带宽度2-4km
        cost = random.uniform(80, 120)
        
        satellites.append(Satellite(
            id=i,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            swath_width=swath_width,
            cost=cost,
            orbit_direction=pattern["angle"]
        ))
    
    # 创建地面传感器
    ground_sensors = []
    for i in range(15):
        x = random.uniform(1, 19)
        y = random.uniform(1, 14)
        radius = random.uniform(1.5, 3.5)
        cost = random.uniform(8, 15)
        mobile = i < 5  # 前5个是可移动的
        move_range = 3.0 if mobile else 0.0
        ground_sensors.append(GroundSensor(i, x, y, radius, cost, mobile=mobile, move_range=move_range))
    
    # 资源约束
    constraints = ResourceConstraints(
        max_satellites=4,
        max_ground_sensors=8,
        max_total_cost=500,
        max_bandwidth=300,
        target_coverage_ratio=0.9
    )
    
    return target_area, satellites, ground_sensors, constraints

def demo_genetic_algorithm():
    """遗传算法演示"""
    print("="*60)
    print("遗传算法传感器网络优化演示")
    print("="*60)
    
    target_area, satellites, ground_sensors, constraints = create_test_scenario()
    
    print(f"场景信息:")
    print(f"- 目标区域面积: {target_area.area:.1f}")
    print(f"- 候选卫星数量: {len(satellites)}")
    print(f"- 候选地面传感器数量: {len(ground_sensors)}")
    print(f"- 目标覆盖率: {constraints.target_coverage_ratio*100}%")
    print(f"- 最大成本: {constraints.max_total_cost}")
    
    # 创建遗传算法优化器
    ga_optimizer = GeneticAlgorithmOptimizer(
        target_area=target_area,
        satellites=satellites,
        ground_sensors=ground_sensors,
        constraints=constraints,
        population_size=30,
        generations=50,
        grid_resolution=0.8
    )
    
    # 执行优化
    best_solution = ga_optimizer.optimize()
    
    # 显示结果
    print(f"\n=== 遗传算法优化结果 ===")
    print(f"选择的卫星: {best_solution.selected_satellites}")
    print(f"选择的地面传感器: {best_solution.selected_ground_sensors}")
    print(f"覆盖率: {best_solution.coverage_ratio*100:.2f}%")
    print(f"总成本: {best_solution.total_cost:.1f}")
    print(f"是否达到目标: {'是' if best_solution.coverage_ratio >= constraints.target_coverage_ratio else '否'}")
    
    # 可视化结果
    ga_optimizer.visualize_solution(best_solution, "遗传算法优化结果")
    
    # 绘制适应度历史
    generations = [h['generation'] for h in ga_optimizer.fitness_history]
    best_fitness = [h['best_fitness'] for h in ga_optimizer.fitness_history]
    avg_fitness = [h['avg_fitness'] for h in ga_optimizer.fitness_history]
    
    plt.figure(figsize=(10, 6))
    plt.plot(generations, best_fitness, 'r-', label='最佳适应度', linewidth=2)
    plt.plot(generations, avg_fitness, 'b--', label='平均适应度', linewidth=2)
    plt.xlabel('代数')
    plt.ylabel('适应度')
    plt.title('遗传算法收敛过程', fontweight='bold')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
    
    return ga_optimizer, best_solution

def demo_simulated_annealing():
    """模拟退火算法演示"""
    print("\n" + "="*60)
    print("模拟退火传感器网络优化演示")
    print("="*60)
    
    target_area, satellites, ground_sensors, constraints = create_test_scenario()
    
    # 创建模拟退火优化器
    sa_optimizer = SimulatedAnnealingOptimizer(
        target_area=target_area,
        satellites=satellites,
        ground_sensors=ground_sensors,
        constraints=constraints,
        initial_temperature=1000.0,
        final_temperature=1.0,
        cooling_rate=0.98,
        max_iterations=500,
        grid_resolution=0.8
    )
    
    # 执行优化
    best_solution = sa_optimizer.optimize()
    
    # 显示结果
    print(f"\n=== 模拟退火优化结果 ===")
    print(f"选择的卫星: {best_solution.selected_satellites}")
    print(f"选择的地面传感器: {best_solution.selected_ground_sensors}")
    print(f"覆盖率: {best_solution.coverage_ratio*100:.2f}%")
    print(f"总成本: {best_solution.total_cost:.1f}")
    print(f"是否达到目标: {'是' if best_solution.coverage_ratio >= constraints.target_coverage_ratio else '否'}")
    
    # 可视化结果
    sa_optimizer.visualize_solution(best_solution, "模拟退火优化结果")
    
    # 绘制温度和适应度历史
    iterations = [h['iteration'] for h in sa_optimizer.temperature_history[::10]]  # 每10个取一个
    temperatures = [h['temperature'] for h in sa_optimizer.temperature_history[::10]]
    best_fitness = [h['best_fitness'] for h in sa_optimizer.temperature_history[::10]]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    ax1.plot(iterations, temperatures, 'r-', linewidth=2)
    ax1.set_ylabel('温度')
    ax1.set_title('模拟退火温度变化', fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(iterations, best_fitness, 'b-', linewidth=2)
    ax2.set_xlabel('迭代次数')
    ax2.set_ylabel('最佳适应度')
    ax2.set_title('模拟退火收敛过程', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return sa_optimizer, best_solution

def demo_resource_balance():
    """资源平衡优化演示"""
    print("\n" + "="*60)
    print("资源平衡优化演示")
    print("="*60)
    
    target_area, satellites, ground_sensors, constraints = create_test_scenario()
    
    # 使用遗传算法作为基础优化器
    base_optimizer = GeneticAlgorithmOptimizer(
        target_area=target_area,
        satellites=satellites,
        ground_sensors=ground_sensors,
        constraints=constraints,
        population_size=20,
        generations=30,
        grid_resolution=0.8
    )
    
    # 创建资源平衡优化器
    resource_optimizer = ResourceBalanceOptimizer(base_optimizer)
    
    # 测试不同预算水平
    budget_levels = [200, 300, 400, 500, 600]
    pareto_solutions = resource_optimizer.multi_objective_optimization(budget_levels)
    
    # 分析边际效率
    marginal_analysis = resource_optimizer.analyze_marginal_efficiency()
    
    print(f"\n=== 边际效率分析 ===")
    if 'marginal_analysis' in marginal_analysis:
        for analysis in marginal_analysis['marginal_analysis']:
            print(f"成本区间 {analysis['cost_range']}: "
                  f"覆盖率提升 {analysis['coverage_increase']:.1f}%, "
                  f"边际效率 {analysis['marginal_efficiency']:.4f}")
        
        if marginal_analysis['best_efficiency_range']:
            best = marginal_analysis['best_efficiency_range']
            print(f"\n最佳效率区间: {best['cost_range']}")
    
    # 可视化帕累托前沿
    resource_optimizer.visualize_pareto_front()
    
    return resource_optimizer, pareto_solutions

def demo_dynamic_adjustment():
    """动态传感器调整演示"""
    print("\n" + "="*60)
    print("动态传感器调整演示")
    print("="*60)
    
    target_area, satellites, ground_sensors, constraints = create_test_scenario()
    
    # 确保有移动传感器
    for i in range(min(5, len(ground_sensors))):
        ground_sensors[i].mobile = True
        ground_sensors[i].move_range = 3.0
    
    # 创建基础优化器（使用较少迭代以加快速度）
    base_optimizer = GeneticAlgorithmOptimizer(
        target_area=target_area,
        satellites=satellites,
        ground_sensors=ground_sensors,
        constraints=constraints,
        population_size=15,
        generations=20,
        grid_resolution=1.0  # 使用较粗网格加快计算
    )
    
    # 创建动态调整器
    dynamic_adjuster = DynamicSensorAdjuster(base_optimizer, time_windows=4)
    
    print(f"可移动传感器数量: {len(dynamic_adjuster.mobile_sensors)}")
    print(f"时间窗口数量: {dynamic_adjuster.time_windows}")
    
    # 执行动态调整
    time_solutions = dynamic_adjuster.dynamic_adjustment()
    
    # 分析移动性需求
    mobility_analysis = dynamic_adjuster.analyze_sensor_mobility(time_solutions)
    
    print(f"\n=== 传感器移动性分析 ===")
    print(f"总重配置次数: {mobility_analysis['total_reconfigurations']}")
    
    for change in mobility_analysis['satellite_changes']:
        if change['change_count'] > 0:
            print(f"卫星变化 {change['time_window']}: "
                  f"添加 {len(change['added'])}, 移除 {len(change['removed'])}")
    
    for change in mobility_analysis['ground_sensor_changes']:
        if change['change_count'] > 0:
            print(f"地面传感器变化 {change['time_window']}: "
                  f"添加 {len(change['added'])}, 移除 {len(change['removed'])}")
    
    # 可视化动态覆盖
    dynamic_adjuster.visualize_dynamic_coverage(time_solutions)
    
    return dynamic_adjuster, time_solutions

def demo_algorithm_comparison():
    """算法性能比较演示"""
    print("\n" + "="*60)
    print("算法性能比较演示")
    print("="*60)
    
    target_area, satellites, ground_sensors, constraints = create_test_scenario()
    
    print("比较遗传算法和模拟退火算法的性能...")
    
    results = []
    
    # 遗传算法
    print("\n--- 遗传算法 ---")
    start_time = time.time()
    ga_optimizer = GeneticAlgorithmOptimizer(
        target_area, satellites, ground_sensors, constraints,
        population_size=20, generations=30, grid_resolution=0.8
    )
    ga_solution = ga_optimizer.optimize()
    ga_time = time.time() - start_time
    
    results.append({
        'algorithm': '遗传算法',
        'coverage': ga_solution.coverage_ratio * 100,
        'cost': ga_solution.total_cost,
        'satellites': len(ga_solution.selected_satellites),
        'ground_sensors': len(ga_solution.selected_ground_sensors),
        'time': ga_time,
        'achieved_target': ga_solution.coverage_ratio >= constraints.target_coverage_ratio
    })
    
    # 模拟退火
    print("\n--- 模拟退火 ---")
    start_time = time.time()
    sa_optimizer = SimulatedAnnealingOptimizer(
        target_area, satellites, ground_sensors, constraints,
        max_iterations=300, grid_resolution=0.8
    )
    sa_solution = sa_optimizer.optimize()
    sa_time = time.time() - start_time
    
    results.append({
        'algorithm': '模拟退火',
        'coverage': sa_solution.coverage_ratio * 100,
        'cost': sa_solution.total_cost,
        'satellites': len(sa_solution.selected_satellites),
        'ground_sensors': len(sa_solution.selected_ground_sensors),
        'time': sa_time,
        'achieved_target': sa_solution.coverage_ratio >= constraints.target_coverage_ratio
    })
    
    # 显示比较结果
    print(f"\n=== 算法性能比较 ===")
    print(f"{'算法':<10} {'覆盖率(%)':<10} {'成本':<8} {'卫星':<6} {'地面站':<8} {'时间(s)':<8} {'达标':<6}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['algorithm']:<10} {result['coverage']:<10.1f} {result['cost']:<8.1f} "
              f"{result['satellites']:<6} {result['ground_sensors']:<8} {result['time']:<8.1f} "
              f"{'是' if result['achieved_target'] else '否':<6}")
    
    # 可视化比较
    algorithms = [r['algorithm'] for r in results]
    coverages = [r['coverage'] for r in results]
    costs = [r['cost'] for r in results]
    times = [r['time'] for r in results]
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # 覆盖率比较
    bars1 = ax1.bar(algorithms, coverages, color=['lightblue', 'lightcoral'])
    ax1.axhline(y=constraints.target_coverage_ratio*100, color='red', linestyle='--', label='目标')
    ax1.set_ylabel('覆盖率 (%)')
    ax1.set_title('覆盖率比较')
    ax1.legend()
    
    # 成本比较
    bars2 = ax2.bar(algorithms, costs, color=['lightgreen', 'gold'])
    ax2.set_ylabel('总成本')
    ax2.set_title('成本比较')
    
    # 时间比较
    bars3 = ax3.bar(algorithms, times, color=['plum', 'orange'])
    ax3.set_ylabel('计算时间 (秒)')
    ax3.set_title('计算时间比较')
    
    # 添加数值标签
    for bars, values in [(bars1, coverages), (bars2, costs), (bars3, times)]:
        for bar, value in zip(bars, values):
            height = bar.get_height()
            bar.axes.text(bar.get_x() + bar.get_width()/2, height + height*0.01,
                         f'{value:.1f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.show()
    
    return results

def main():
    """主演示函数"""
    print("空间-地面传感器网络启发式优化算法演示")
    print("="*80)
    
    # 设置随机种子以获得可重复的结果
    random.seed(42)
    np.random.seed(42)
    
    try:
        # 1. 遗传算法演示
        ga_optimizer, ga_solution = demo_genetic_algorithm()
        
        # 2. 模拟退火演示
        sa_optimizer, sa_solution = demo_simulated_annealing()
        
        # 3. 资源平衡优化演示
        resource_optimizer, pareto_solutions = demo_resource_balance()
        
        # 4. 动态传感器调整演示
        dynamic_adjuster, time_solutions = demo_dynamic_adjustment()
        
        # 5. 算法性能比较
        comparison_results = demo_algorithm_comparison()
        
        print(f"\n" + "="*80)
        print("所有演示完成！")
        print("="*80)
        
        print(f"\n功能总结:")
        print(f"1. 遗传算法优化 - 群体智能搜索最优传感器配置")
        print(f"2. 模拟退火优化 - 随机搜索避免局部最优")
        print(f"3. 资源平衡优化 - 多目标帕累托前沿分析")
        print(f"4. 动态调整优化 - 时变需求的自适应传感器配置")
        print(f"5. 算法性能比较 - 不同启发式算法的效果对比")
        print(f"6. 支持卫星和地面传感器混合选择")
        print(f"7. 考虑多种资源约束（成本、带宽、数量限制等）")
        print(f"8. 提供详细的可视化和分析功能")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()