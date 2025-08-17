"""
卫星+地面混合传感器位置优化模块

该模块用于优化已有卫星和地面传感器的位置配置，在不增加传感器数量的情况下
通过重新配置传感器参数来提高覆盖率。

主要功能：
1. 评估现有混合传感器部署方案
2. 基于遗传算法和模拟退火的位置优化
3. 卫星轨道参数和地面传感器位置同步优化
4. 优化前后对比分析

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
class HybridOptimizationSolution:
    """混合传感器优化结果"""
    original_satellites: List[Satellite]
    original_ground_sensors: List[GroundSensor]
    optimized_satellites: List[Satellite]
    optimized_ground_sensors: List[GroundSensor]
    original_coverage: float
    optimized_coverage: float
    improvement_ratio: float
    optimization_time: float
    optimization_method: str

class HybridSensorPositionOptimizer:
    """卫星+地面混合传感器位置优化器"""
    
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
                          ground_sensors: List[GroundSensor]) -> float:
        """
        评估当前部署方案的覆盖率
        
        参数:
            satellites: 卫星列表
            ground_sensors: 地面传感器列表
            
        返回:
            覆盖率 (0-1之间)
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
        
        return len(covered_points) / len(self.grid_points) if self.grid_points else 0.0
    
    def optimize_positions_genetic(self, satellites: List[Satellite], 
                                 ground_sensors: List[GroundSensor],
                                 generations: int = 50,
                                 population_size: int = 30) -> HybridOptimizationSolution:
        """
        使用遗传算法优化混合传感器位置
        
        参数:
            satellites: 原始卫星列表
            ground_sensors: 原始地面传感器列表
            generations: 遗传算法代数
            population_size: 种群大小
            
        返回:
            优化结果
        """
        print(f"开始使用遗传算法优化混合传感器位置...")
        print(f"卫星: {len(satellites)} 个, 地面传感器: {len(ground_sensors)} 个")
        
        start_time = time.time()
        
        # 评估原始方案
        original_coverage = self.evaluate_deployment(satellites, ground_sensors)
        print(f"原始覆盖率: {original_coverage*100:.2f}%")
        
        # 获取区域边界用于生成候选位置
        minx, miny, maxx, maxy = self.target_area.bounds
        
        def create_individual():
            """创建一个个体（候选解）"""
            individual = []
            
            # 编码卫星参数: [start_x, start_y, end_x, end_y, swath_width]
            for sat in satellites:
                start_x = np.random.uniform(minx, maxx)
                start_y = np.random.uniform(miny, maxy)
                end_x = np.random.uniform(minx, maxx)
                end_y = np.random.uniform(miny, maxy)
                swath_width = np.random.uniform(1.0, 5.0)
                individual.extend([start_x, start_y, end_x, end_y, swath_width])
            
            # 编码地面传感器参数: [x, y, radius]
            for sensor in ground_sensors:
                x = np.random.uniform(minx, maxx)
                y = np.random.uniform(miny, maxy)
                radius = np.random.uniform(0.5, 4.0)
                individual.extend([x, y, radius])
            
            return individual
        
        def decode_individual(individual):
            """解码个体为传感器配置"""
            decoded_satellites = []
            decoded_sensors = []
            
            idx = 0
            # 解码卫星
            for i, sat in enumerate(satellites):
                start_x = individual[idx]
                start_y = individual[idx + 1]
                end_x = individual[idx + 2]
                end_y = individual[idx + 3]
                swath_width = individual[idx + 4]
                
                new_sat = Satellite(sat.id, start_x, start_y, end_x, end_y, 
                                  swath_width, sat.cost)
                decoded_satellites.append(new_sat)
                idx += 5
            
            # 解码地面传感器
            for i, sensor in enumerate(ground_sensors):
                x = individual[idx]
                y = individual[idx + 1]
                radius = individual[idx + 2]
                
                new_sensor = GroundSensor(sensor.id, x, y, radius, sensor.cost)
                decoded_sensors.append(new_sensor)
                idx += 3
            
            return decoded_satellites, decoded_sensors
        
        def fitness_function(individual):
            """适应度函数"""
            decoded_sats, decoded_sensors = decode_individual(individual)
            coverage = self.evaluate_deployment(decoded_sats, decoded_sensors)
            return coverage
        
        def crossover(parent1, parent2):
            """交叉操作"""
            if len(parent1) != len(parent2):
                return parent1, parent2
            
            crossover_point = random.randint(1, len(parent1) - 1)
            child1 = parent1[:crossover_point] + parent2[crossover_point:]
            child2 = parent2[:crossover_point] + parent1[crossover_point:]
            return child1, child2
        
        def mutate(individual, mutation_rate=0.1):
            """变异操作"""
            mutated = individual.copy()
            for i in range(len(mutated)):
                if random.random() < mutation_rate:
                    # 根据参数类型进行不同的变异
                    if i % 5 < 4 or (i >= len(satellites)*5 and (i - len(satellites)*5) % 3 < 2):
                        # 位置参数：在合理范围内变异
                        mutated[i] += np.random.normal(0, (maxx - minx) * 0.1)
                        mutated[i] = np.clip(mutated[i], minx, maxx)
                    else:
                        # 半径或宽度参数
                        mutated[i] += np.random.normal(0, 0.5)
                        mutated[i] = max(0.5, mutated[i])
            return mutated
        
        # 初始化种群
        population = [create_individual() for _ in range(population_size)]
        
        best_solution = None
        best_fitness = 0
        
        # 进化过程
        for generation in range(generations):
            # 计算适应度
            fitness_scores = [fitness_function(ind) for ind in population]
            
            # 记录最佳解
            max_fitness_idx = np.argmax(fitness_scores)
            if fitness_scores[max_fitness_idx] > best_fitness:
                best_fitness = fitness_scores[max_fitness_idx]
                best_solution = population[max_fitness_idx].copy()
            
            if generation % 10 == 0:
                print(f"第 {generation} 代, 最佳覆盖率: {best_fitness*100:.2f}%")
            
            # 选择
            new_population = []
            for _ in range(population_size // 2):
                # 锦标赛选择
                tournament_size = 3
                tournament_indices = random.sample(range(population_size), tournament_size)
                winner_idx = max(tournament_indices, key=lambda x: fitness_scores[x])
                new_population.append(population[winner_idx])
            
            # 交叉和变异
            while len(new_population) < population_size:
                parent1, parent2 = random.sample(new_population[:population_size//2], 2)
                child1, child2 = crossover(parent1, parent2)
                child1 = mutate(child1)
                child2 = mutate(child2)
                new_population.extend([child1, child2])
            
            population = new_population[:population_size]
        
        # 解码最佳解
        optimized_sats, optimized_sensors = decode_individual(best_solution)
        optimization_time = time.time() - start_time
        
        # 计算最终覆盖率
        final_coverage = self.evaluate_deployment(optimized_sats, optimized_sensors)
        improvement = (final_coverage - original_coverage) / original_coverage * 100 if original_coverage > 0 else 0
        
        print(f"优化完成!")
        print(f"优化后覆盖率: {final_coverage*100:.2f}%")
        print(f"改进幅度: {improvement:.2f}%")
        print(f"优化时间: {optimization_time:.1f}秒")
        
        return HybridOptimizationSolution(
            original_satellites=satellites,
            original_ground_sensors=ground_sensors,
            optimized_satellites=optimized_sats,
            optimized_ground_sensors=optimized_sensors,
            original_coverage=original_coverage,
            optimized_coverage=final_coverage,
            improvement_ratio=improvement,
            optimization_time=optimization_time,
            optimization_method="遗传算法"
        )
    
    def optimize_positions_annealing(self, satellites: List[Satellite], 
                                   ground_sensors: List[GroundSensor],
                                   max_iterations: int = 1000) -> HybridOptimizationSolution:
        """
        使用模拟退火算法优化混合传感器位置
        
        参数:
            satellites: 原始卫星列表
            ground_sensors: 原始地面传感器列表
            max_iterations: 最大迭代次数
            
        返回:
            优化结果
        """
        print(f"开始使用模拟退火算法优化混合传感器位置...")
        
        start_time = time.time()
        
        # 评估原始方案
        original_coverage = self.evaluate_deployment(satellites, ground_sensors)
        print(f"原始覆盖率: {original_coverage*100:.2f}%")
        
        # 获取区域边界
        minx, miny, maxx, maxy = self.target_area.bounds
        
        # 当前解（复制原始方案）
        current_sats = [Satellite(s.id, s.start_x, s.start_y, s.end_x, s.end_y, 
                                 s.swath_width, s.cost) for s in satellites]
        current_sensors = [GroundSensor(s.id, s.x, s.y, s.radius, s.cost) 
                          for s in ground_sensors]
        
        current_coverage = original_coverage
        best_sats = [Satellite(s.id, s.start_x, s.start_y, s.end_x, s.end_y, 
                              s.swath_width, s.cost) for s in satellites]
        best_sensors = [GroundSensor(s.id, s.x, s.y, s.radius, s.cost) 
                       for s in ground_sensors]
        best_coverage = original_coverage
        
        # 模拟退火参数
        initial_temp = 1.0
        final_temp = 0.01
        cooling_rate = (final_temp / initial_temp) ** (1.0 / max_iterations)
        current_temp = initial_temp
        
        for iteration in range(max_iterations):
            # 生成邻域解
            new_sats = [Satellite(s.id, s.start_x, s.start_y, s.end_x, s.end_y, 
                                 s.swath_width, s.cost) for s in current_sats]
            new_sensors = [GroundSensor(s.id, s.x, s.y, s.radius, s.cost) 
                          for s in current_sensors]
            
            # 随机选择要修改的传感器
            if random.random() < 0.5 and new_sats:
                # 修改卫星
                sat_idx = random.randint(0, len(new_sats) - 1)
                sat = new_sats[sat_idx]
                
                # 小幅度调整轨道参数
                adjustment = np.random.normal(0, (maxx - minx) * 0.05)
                if random.random() < 0.25:
                    sat.start_x = np.clip(sat.start_x + adjustment, minx, maxx)
                elif random.random() < 0.5:
                    sat.start_y = np.clip(sat.start_y + adjustment, miny, maxy)
                elif random.random() < 0.75:
                    sat.end_x = np.clip(sat.end_x + adjustment, minx, maxx)
                else:
                    sat.end_y = np.clip(sat.end_y + adjustment, miny, maxy)
                    
            elif new_sensors:
                # 修改地面传感器
                sensor_idx = random.randint(0, len(new_sensors) - 1)
                sensor = new_sensors[sensor_idx]
                
                # 小幅度调整位置或半径
                adjustment = np.random.normal(0, (maxx - minx) * 0.05)
                if random.random() < 0.4:
                    sensor.x = np.clip(sensor.x + adjustment, minx, maxx)
                elif random.random() < 0.8:
                    sensor.y = np.clip(sensor.y + adjustment, miny, maxy)
                else:
                    sensor.radius = max(0.5, sensor.radius + np.random.normal(0, 0.2))
            
            # 评估新解
            new_coverage = self.evaluate_deployment(new_sats, new_sensors)
            
            # 决定是否接受新解
            if new_coverage > current_coverage:
                # 更好的解，直接接受
                current_sats = new_sats
                current_sensors = new_sensors
                current_coverage = new_coverage
                
                if new_coverage > best_coverage:
                    best_sats = [Satellite(s.id, s.start_x, s.start_y, s.end_x, s.end_y, 
                                          s.swath_width, s.cost) for s in new_sats]
                    best_sensors = [GroundSensor(s.id, s.x, s.y, s.radius, s.cost) 
                                   for s in new_sensors]
                    best_coverage = new_coverage
            else:
                # 较差的解，根据温度概率接受
                delta = new_coverage - current_coverage
                probability = np.exp(delta / current_temp)
                if random.random() < probability:
                    current_sats = new_sats
                    current_sensors = new_sensors
                    current_coverage = new_coverage
            
            # 降温
            current_temp *= cooling_rate
            
            if iteration % 100 == 0:
                print(f"迭代 {iteration}, 当前覆盖率: {current_coverage*100:.2f}%, "
                      f"最佳覆盖率: {best_coverage*100:.2f}%, 温度: {current_temp:.4f}")
        
        optimization_time = time.time() - start_time
        improvement = (best_coverage - original_coverage) / original_coverage * 100 if original_coverage > 0 else 0
        
        print(f"优化完成!")
        print(f"优化后覆盖率: {best_coverage*100:.2f}%")
        print(f"改进幅度: {improvement:.2f}%")
        print(f"优化时间: {optimization_time:.1f}秒")
        
        return HybridOptimizationSolution(
            original_satellites=satellites,
            original_ground_sensors=ground_sensors,
            optimized_satellites=best_sats,
            optimized_ground_sensors=best_sensors,
            original_coverage=original_coverage,
            optimized_coverage=best_coverage,
            improvement_ratio=improvement,
            optimization_time=optimization_time,
            optimization_method="模拟退火"
        )
    
    def visualize_optimization_result(self, solution: HybridOptimizationSolution, 
                                    title: str = "混合传感器位置优化结果"):
        """可视化优化结果"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        
        # 绘制原始方案
        self._plot_deployment(ax1, solution.original_satellites, 
                             solution.original_ground_sensors,
                             f"原始方案 (覆盖率: {solution.original_coverage*100:.1f}%)")
        
        # 绘制优化方案
        self._plot_deployment(ax2, solution.optimized_satellites, 
                             solution.optimized_ground_sensors,
                             f"优化方案 (覆盖率: {solution.optimized_coverage*100:.1f}%)")
        
        plt.suptitle(f"{title}\n改进: {solution.improvement_ratio:.1f}% | "
                    f"方法: {solution.optimization_method} | "
                    f"时间: {solution.optimization_time:.1f}s", fontsize=14)
        plt.tight_layout()
        plt.show()
    
    def _plot_deployment(self, ax, satellites: List[Satellite], 
                        ground_sensors: List[GroundSensor], title: str):
        """绘制部署方案"""
        # 绘制目标区域
        x_coords, y_coords = self.target_area.exterior.xy
        ax.plot(x_coords, y_coords, 'b-', linewidth=2, label='目标区域')
        ax.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
        
        # 绘制卫星覆盖
        for i, sat in enumerate(satellites):
            coverage = sat.get_coverage_area()
            if coverage and not coverage.is_empty:
                x_coords, y_coords = coverage.exterior.xy
                ax.plot(x_coords, y_coords, 'r-', alpha=0.7, linewidth=1)
                ax.fill(x_coords, y_coords, alpha=0.2, color='red')
                
                # 标注卫星轨道
                ax.plot([sat.start_x, sat.end_x], [sat.start_y, sat.end_y], 
                       'r-', linewidth=3, alpha=0.8)
                ax.text((sat.start_x + sat.end_x)/2, (sat.start_y + sat.end_y)/2, 
                       f'S{i+1}', fontsize=8, ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.2', facecolor='red', alpha=0.7))
        
        # 绘制地面传感器
        for i, sensor in enumerate(ground_sensors):
            circle = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                              fill=False, color='green', alpha=0.7, linewidth=1.5)
            ax.add_patch(circle)
            
            circle_fill = plt.Circle((sensor.x, sensor.y), sensor.radius, 
                                   fill=True, color='green', alpha=0.2)
            ax.add_patch(circle_fill)
            
            ax.plot(sensor.x, sensor.y, 'go', markersize=8)
            ax.text(sensor.x, sensor.y + sensor.radius + 0.3, f'G{i+1}', 
                   fontsize=8, ha='center', va='bottom',
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='green', alpha=0.7))
        
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


def demo_hybrid_sensor_position_optimize():
    """演示混合传感器位置优化"""
    print("="*60)
    print("混合传感器位置优化演示（不增补传感器）")
    print("="*60)
    
    # 创建目标区域
    target_area = Polygon([(0, 0), (12, 0), (12, 10), (0, 10)])
    
    # 创建一个次优的现有部署方案
    existing_satellites = [
        Satellite(0, start_x=2, start_y=0, end_x=4, end_y=10, swath_width=2, cost=80),
        Satellite(1, start_x=8, start_y=0, end_x=10, end_y=10, swath_width=2, cost=90),
    ]
    
    existing_ground_sensors = [
        GroundSensor(0, 3, 3, 1.5, cost=10),
        GroundSensor(1, 9, 3, 1.5, cost=12),
        GroundSensor(2, 3, 7, 1.5, cost=11),
        GroundSensor(3, 9, 7, 1.5, cost=13),
    ]
    
    print(f"现有部署方案:")
    print(f"- 卫星: {len(existing_satellites)} 个")
    print(f"- 地面传感器: {len(existing_ground_sensors)} 个")
    
    # 创建优化器
    optimizer = HybridSensorPositionOptimizer(target_area, grid_resolution=0.4)
    
    # 评估原始方案
    original_coverage = optimizer.evaluate_deployment(existing_satellites, existing_ground_sensors)
    print(f"- 原始覆盖率: {original_coverage*100:.2f}%")
    
    # 方法1：遗传算法优化
    print(f"\n方法1：遗传算法优化")
    ga_solution = optimizer.optimize_positions_genetic(
        existing_satellites, existing_ground_sensors,
        generations=30, population_size=20
    )
    
    # 方法2：模拟退火优化
    print(f"\n方法2：模拟退火算法优化")
    sa_solution = optimizer.optimize_positions_annealing(
        existing_satellites, existing_ground_sensors,
        max_iterations=500
    )
    
    # 比较结果
    print(f"\n" + "="*50)
    print(f"优化结果比较")
    print(f"="*50)
    print(f"{'指标':<15} {'原始方案':<12} {'遗传算法':<12} {'模拟退火':<12}")
    print(f"-" * 55)
    print(f"{'覆盖率(%)':<15} {original_coverage*100:<12.1f} {ga_solution.optimized_coverage*100:<12.1f} {sa_solution.optimized_coverage*100:<12.1f}")
    print(f"{'改进幅度(%)':<15} {0:<12.1f} {ga_solution.improvement_ratio:<12.1f} {sa_solution.improvement_ratio:<12.1f}")
    print(f"{'优化时间(s)':<15} {'-':<12} {ga_solution.optimization_time:<12.1f} {sa_solution.optimization_time:<12.1f}")
    
    # 选择最佳方案进行可视化
    best_solution = ga_solution if ga_solution.optimized_coverage > sa_solution.optimized_coverage else sa_solution
    
    print(f"\n最佳方案: {best_solution.optimization_method}")
    optimizer.visualize_optimization_result(best_solution)
    
    return optimizer, ga_solution, sa_solution


if __name__ == "__main__":
    demo_hybrid_sensor_position_optimize()