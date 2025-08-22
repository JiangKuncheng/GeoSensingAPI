"""
卫星+地面混合传感器从零布设优化模块

该模块实现了卫星传感器和地面传感器的混合选择优化，
使用遗传算法和模拟退火算法解决大规模传感器网络选址问题。

主要功能：
1. 卫星和地面传感器混合选择优化
2. 资源约束下的覆盖最大化
3. 多目标优化（覆盖率 vs 成本）
4. 启发式算法求解

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
    swath_width: float  # 条带宽度
    cost: float = 100.0
    
    def get_coverage_area(self) -> Polygon:
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
class ResourceConstraints:
    """资源约束条件"""
    max_satellites: int = 10
    max_ground_sensors: int = 20
    max_total_cost: float = 1000.0
    target_coverage_ratio: float = 0.9

class SensorSelectionSolution:
    """传感器选择方案"""
    def __init__(self):
        self.selected_satellites: List[int] = []
        self.selected_ground_sensors: List[int] = []
        self.fitness: float = 0.0
        self.coverage_ratio: float = 0.0
        self.total_cost: float = 0.0
        self.penalty: float = 0.0
    
    def copy(self):
        """创建解的副本"""
        new_solution = SensorSelectionSolution()
        new_solution.selected_satellites = self.selected_satellites.copy()
        new_solution.selected_ground_sensors = self.selected_ground_sensors.copy()
        new_solution.fitness = self.fitness
        new_solution.coverage_ratio = self.coverage_ratio
        new_solution.total_cost = self.total_cost
        new_solution.penalty = self.penalty
        return new_solution

class HybridSensorFromScratchOptimizer:
    """
    卫星+地面混合传感器从零布设优化器
    """
    
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
            satellite_coverage = satellite.get_coverage_area()
            for i, (x, y) in enumerate(self.grid_points):
                if satellite_coverage.contains(Point(x, y)):
                    covered_points.add(i)
        
        # 计算地面传感器覆盖
        for sensor_id in solution.selected_ground_sensors:
            sensor = self.ground_sensors[sensor_id]
            sensor_point = Point(sensor.x, sensor.y)
            for i, (x, y) in enumerate(self.grid_points):
                if sensor_point.distance(Point(x, y)) <= sensor.radius:
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
    
    def evaluate_solution(self, solution: SensorSelectionSolution) -> float:
        """评估解的适应度"""
        solution.coverage_ratio = self.calculate_coverage_ratio(solution)
        solution.total_cost = self.calculate_total_cost(solution)
        
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
    
    def optimize_genetic(self, population_size: int = 30, generations: int = 50) -> SensorSelectionSolution:
        """使用遗传算法优化"""
        print("开始遗传算法优化...")
        start_time = time.time()
        
        # 初始化种群
        population = []
        for _ in range(population_size):
            solution = SensorSelectionSolution()
            
            # 随机选择卫星
            num_satellites = random.randint(0, min(len(self.satellites), self.constraints.max_satellites))
            solution.selected_satellites = random.sample(range(len(self.satellites)), num_satellites)
            
            # 随机选择地面传感器
            num_ground_sensors = random.randint(0, min(len(self.ground_sensors), self.constraints.max_ground_sensors))
            solution.selected_ground_sensors = random.sample(range(len(self.ground_sensors)), num_ground_sensors)
            
            self.evaluate_solution(solution)
            population.append(solution)
        
        best_solution = max(population, key=lambda x: x.fitness).copy()
        print(f"初始种群最佳适应度: {best_solution.fitness:.2f}, 覆盖率: {best_solution.coverage_ratio*100:.1f}%")
        
        # 进化过程
        for generation in range(generations):
            new_population = []
            
            # 精英保留
            elite_size = max(1, population_size // 10)
            elite = sorted(population, key=lambda x: x.fitness, reverse=True)[:elite_size]
            new_population.extend([sol.copy() for sol in elite])
            
            # 生成新个体
            while len(new_population) < population_size:
                parent1 = self._tournament_selection(population)
                parent2 = self._tournament_selection(population)
                
                if random.random() < 0.8:  # 交叉概率
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                self._mutate(child1)
                self._mutate(child2)
                
                self.evaluate_solution(child1)
                self.evaluate_solution(child2)
                
                new_population.extend([child1, child2])
            
            # 更新种群
            population = new_population[:population_size]
            
            # 更新最佳解
            current_best = max(population, key=lambda x: x.fitness)
            if current_best.fitness > best_solution.fitness:
                best_solution = current_best.copy()
            
            if generation % 10 == 0:
                print(f"第 {generation} 代: 最佳适应度={best_solution.fitness:.2f}, "
                      f"覆盖率={best_solution.coverage_ratio*100:.1f}%, "
                      f"成本={best_solution.total_cost:.1f}")
        
        end_time = time.time()
        print(f"遗传算法优化完成，耗时: {end_time - start_time:.2f} 秒")
        print(f"最终结果: 覆盖率={best_solution.coverage_ratio*100:.2f}%, "
              f"卫星数量={len(best_solution.selected_satellites)}, "
              f"地面传感器数量={len(best_solution.selected_ground_sensors)}, "
              f"总成本={best_solution.total_cost:.1f}")
        
        return best_solution
    
    def _tournament_selection(self, population: List[SensorSelectionSolution], tournament_size: int = 3) -> SensorSelectionSolution:
        """锦标赛选择"""
        tournament = random.sample(population, min(tournament_size, len(population)))
        return max(tournament, key=lambda x: x.fitness)
    
    def _crossover(self, parent1: SensorSelectionSolution, parent2: SensorSelectionSolution) -> Tuple[SensorSelectionSolution, SensorSelectionSolution]:
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
    
    def _mutate(self, solution: SensorSelectionSolution, mutation_rate: float = 0.1):
        """变异操作"""
        # 卫星变异
        if random.random() < mutation_rate:
            if solution.selected_satellites and random.random() < 0.5:
                # 移除一个卫星
                solution.selected_satellites.remove(random.choice(solution.selected_satellites))
            else:
                # 添加一个卫星
                available = [i for i in range(len(self.satellites)) if i not in solution.selected_satellites]
                if available and len(solution.selected_satellites) < self.constraints.max_satellites:
                    solution.selected_satellites.append(random.choice(available))
        
        # 地面传感器变异
        if random.random() < mutation_rate:
            if solution.selected_ground_sensors and random.random() < 0.5:
                # 移除一个传感器
                solution.selected_ground_sensors.remove(random.choice(solution.selected_ground_sensors))
            else:
                # 添加一个传感器
                available = [i for i in range(len(self.ground_sensors)) if i not in solution.selected_ground_sensors]
                if available and len(solution.selected_ground_sensors) < self.constraints.max_ground_sensors:
                    solution.selected_ground_sensors.append(random.choice(available))
    
    def visualize_solution(self, solution: SensorSelectionSolution, title: str = "混合传感器网络配置"):
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
            swath_polygon = satellite.get_coverage_area()
            
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
            center_x = (satellite.start_x + satellite.end_x) / 2
            center_y = (satellite.start_y + satellite.end_y) / 2
            ax.annotate(f'S{satellite.id}', 
                       (center_x, center_y), 
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


def demo_hybrid_sensor_from_scratch():
    """演示卫星+地面混合传感器从零布设"""
    print("="*60)
    print("卫星+地面混合传感器从零布设演示")
    print("="*60)
    
    # 创建目标区域
    target_area = Polygon([(0, 0), (20, 0), (20, 15), (0, 15)])
    
    # 创建卫星传感器候选（条带状覆盖）
    satellites = [
        Satellite(0, start_x=2, start_y=0, end_x=4, end_y=15, swath_width=3, cost=80),
        Satellite(1, start_x=8, start_y=0, end_x=10, end_y=15, swath_width=3, cost=90),
        Satellite(2, start_x=16, start_y=0, end_x=18, end_y=15, swath_width=3, cost=85),
        Satellite(3, start_x=0, start_y=4, end_x=20, end_y=6, swath_width=2.5, cost=95),
        Satellite(4, start_x=0, start_y=10, end_x=20, end_y=12, swath_width=2.5, cost=88),
    ]
    
    # 创建地面传感器候选
    ground_sensors = [
        GroundSensor(0, 3, 3, 2.0, cost=10),
        GroundSensor(1, 7, 3, 2.0, cost=12),
        GroundSensor(2, 13, 3, 2.0, cost=11),
        GroundSensor(3, 17, 3, 2.0, cost=13),
        GroundSensor(4, 3, 8, 2.0, cost=15),
        GroundSensor(5, 7, 8, 2.0, cost=14),
        GroundSensor(6, 13, 8, 2.0, cost=12),
        GroundSensor(7, 17, 8, 2.0, cost=16),
        GroundSensor(8, 3, 13, 2.0, cost=13),
        GroundSensor(9, 7, 13, 2.0, cost=11),
        GroundSensor(10, 13, 13, 2.0, cost=14),
        GroundSensor(11, 17, 13, 2.0, cost=15),
    ]
    
    # 设置约束
    constraints = ResourceConstraints(
        max_satellites=3,
        max_ground_sensors=6,
        max_total_cost=400,
        target_coverage_ratio=0.85
    )
    
    print(f"场景信息:")
    print(f"- 目标区域: 20x15 矩形")
    print(f"- 候选卫星: {len(satellites)} 个")
    print(f"- 候选地面传感器: {len(ground_sensors)} 个")
    print(f"- 目标覆盖率: {constraints.target_coverage_ratio*100}%")
    print(f"- 成本预算: {constraints.max_total_cost}")
    
    # 创建优化器
    optimizer = HybridSensorFromScratchOptimizer(
        target_area=target_area,
        satellites=satellites,
        ground_sensors=ground_sensors,
        constraints=constraints,
        grid_resolution=0.6
    )
    
    # 使用遗传算法优化
    solution = optimizer.optimize_genetic(population_size=25, generations=40)
    
    print(f"\n优化结果:")
    print(f"- 选择的卫星: {solution.selected_satellites}")
    print(f"- 选择的地面传感器: {solution.selected_ground_sensors}")
    print(f"- 覆盖率: {solution.coverage_ratio*100:.1f}%")
    print(f"- 总成本: {solution.total_cost:.1f}")
    print(f"- 达到目标: {'是' if solution.coverage_ratio >= constraints.target_coverage_ratio else '否'}")
    
    # 可视化结果
    optimizer.visualize_solution(solution, "混合传感器从零布设结果")
    
    return optimizer, solution


if __name__ == "__main__":
    demo_hybrid_sensor_from_scratch()