"""
地面传感器从零布设优化模块

该模块实现了基于贪心算法的地面观测站布设方案，能够在给定的目标区域内
找到最少数量的观测站位置，以满足指定的覆盖比例要求。

主要功能：
1. 目标区域的网格离散化
2. 基于贪心算法的观测站选址
3. 覆盖率计算和验证
4. 可视化展示结果

作者：GeoSensingAPI
"""

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from typing import List, Tuple, Dict
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

class GroundSensorFromScratchSolver:
    """
    地面传感器从零布设求解器
    
    使用贪心算法解决最大覆盖位置问题，为指定区域找到最优的观测站布设方案。
    """
    
    def __init__(self, target_area_coords: List[Tuple[float, float]], 
                 coverage_ratio: float, sensor_radius: float,
                 grid_resolution: float = 0.5):
        """
        初始化求解器
        
        参数:
            target_area_coords: 目标区域的坐标点列表 [(x1,y1), (x2,y2), ...]
            coverage_ratio: 要求的覆盖比例 (0-1之间)
            sensor_radius: 每个观测站的观测半径
            grid_resolution: 网格分辨率，越小精度越高但计算越慢
        """
        self.target_area_coords = target_area_coords
        self.coverage_ratio = coverage_ratio
        self.sensor_radius = sensor_radius
        self.grid_resolution = grid_resolution
        
        # 创建目标区域的多边形
        self.target_area = Polygon(target_area_coords)
        
        # 网格点和相关数据
        self.grid_points = []
        self.grid_weights = []
        self.covered_points = set()
        self.station_locations = []
        
        # 初始化网格
        self._initialize_grid()
        
    def _initialize_grid(self):
        """初始化目标区域的网格点"""
        # 获取区域边界
        minx, miny, maxx, maxy = self.target_area.bounds
        
        # 生成网格点
        x_coords = np.arange(minx, maxx + self.grid_resolution, self.grid_resolution)
        y_coords = np.arange(miny, maxy + self.grid_resolution, self.grid_resolution)
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                if self.target_area.contains(point) or self.target_area.touches(point):
                    self.grid_points.append((x, y))
                    # 每个网格点的权重（可以根据实际需求调整）
                    self.grid_weights.append(1.0)
        
        print(f"网格初始化完成，共生成 {len(self.grid_points)} 个网格点")
        
    def _calculate_coverage_for_position(self, station_pos: Tuple[float, float]) -> set:
        """
        计算在指定位置放置观测站能覆盖的网格点
        
        参数:
            station_pos: 观测站位置 (x, y)
            
        返回:
            被覆盖的网格点索引集合
        """
        covered_indices = set()
        station_point = Point(station_pos)
        
        for i, grid_point in enumerate(self.grid_points):
            if i not in self.covered_points:  # 只考虑未被覆盖的点
                grid_point_geom = Point(grid_point)
                if station_point.distance(grid_point_geom) <= self.sensor_radius:
                    covered_indices.add(i)
                    
        return covered_indices
    
    def _get_candidate_positions(self) -> List[Tuple[float, float]]:
        """
        生成候选观测站位置
        
        这里使用网格点作为候选位置，实际应用中可以使用更复杂的策略
        """
        # 可以使用网格点作为候选位置
        candidates = []
        minx, miny, maxx, maxy = self.target_area.bounds
        
        # 生成候选位置网格（可以比目标区域网格更稀疏）
        candidate_resolution = self.grid_resolution * 2  # 候选位置网格更稀疏
        x_coords = np.arange(minx, maxx + candidate_resolution, candidate_resolution)
        y_coords = np.arange(miny, maxy + candidate_resolution, candidate_resolution)
        
        for x in x_coords:
            for y in y_coords:
                point = Point(x, y)
                # 候选位置可以在区域内或边界附近
                if (self.target_area.contains(point) or 
                    self.target_area.distance(point) <= self.sensor_radius):
                    candidates.append((x, y))
                    
        return candidates
    
    def solve(self) -> Tuple[List[Tuple[float, float]], int, float]:
        """
        使用贪心算法求解观测站布设问题
        
        返回:
            观测站位置列表, 观测站数量, 实际覆盖率
        """
        print("开始求解观测站布设问题...")
        
        total_points = len(self.grid_points)
        required_coverage = int(total_points * self.coverage_ratio)
        
        print(f"目标区域总网格点数: {total_points}")
        print(f"要求覆盖点数: {required_coverage} (覆盖率: {self.coverage_ratio*100:.1f}%)")
        
        # 获取候选位置
        candidate_positions = self._get_candidate_positions()
        print(f"候选观测站位置数: {len(candidate_positions)}")
        
        self.station_locations = []
        self.covered_points = set()
        iteration = 0
        
        while len(self.covered_points) < required_coverage:
            iteration += 1
            best_position = None
            best_new_coverage = 0
            best_covered_set = set()
            
            # 评估每个候选位置
            for pos in candidate_positions:
                new_coverage = self._calculate_coverage_for_position(pos)
                new_coverage_count = len(new_coverage)
                
                if new_coverage_count > best_new_coverage:
                    best_new_coverage = new_coverage_count
                    best_position = pos
                    best_covered_set = new_coverage
            
            if best_position is None or best_new_coverage == 0:
                print("警告: 无法找到更多有效的观测站位置")
                break
                
            # 添加最佳位置
            self.station_locations.append(best_position)
            self.covered_points.update(best_covered_set)
            
            current_coverage_ratio = len(self.covered_points) / total_points
            print(f"第 {iteration} 个观测站: {best_position}, "
                  f"新增覆盖: {best_new_coverage} 点, "
                  f"总覆盖率: {current_coverage_ratio*100:.2f}%")
        
        final_coverage_ratio = len(self.covered_points) / total_points
        print(f"\n求解完成!")
        print(f"观测站数量: {len(self.station_locations)}")
        print(f"最终覆盖率: {final_coverage_ratio*100:.2f}%")
        
        return self.station_locations, len(self.station_locations), final_coverage_ratio
    
    def visualize(self, show_grid: bool = False, save_path: str = None):
        """
        可视化观测站布设结果
        
        参数:
            show_grid: 是否显示网格点
            save_path: 保存图片的路径，None则不保存
        """
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        
        # 绘制目标区域
        x_coords, y_coords = zip(*self.target_area_coords)
        ax.plot(list(x_coords) + [x_coords[0]], 
                list(y_coords) + [y_coords[0]], 
                'b-', linewidth=2, label='目标区域边界')
        ax.fill(x_coords, y_coords, alpha=0.3, color='lightblue', label='目标区域')
        
        # 绘制网格点（如果需要）
        if show_grid:
            grid_x, grid_y = zip(*self.grid_points)
            ax.scatter(grid_x, grid_y, c='lightgray', s=1, alpha=0.5, label='网格点')
        
        # 绘制观测站覆盖范围
        for i, station in enumerate(self.station_locations):
            circle = plt.Circle(station, self.sensor_radius, 
                              fill=False, color='red', alpha=0.6, linewidth=1.5)
            ax.add_patch(circle)
            
            # 绘制覆盖区域填充
            circle_fill = plt.Circle(station, self.sensor_radius, 
                                   fill=True, color='red', alpha=0.1)
            ax.add_patch(circle_fill)
        
        # 绘制观测站位置
        if self.station_locations:
            station_x, station_y = zip(*self.station_locations)
            ax.scatter(station_x, station_y, c='red', s=100, 
                      marker='s', label=f'观测站 ({len(self.station_locations)}个)', 
                      edgecolors='black', linewidth=1, zorder=5)
            
            # 标注观测站编号
            for i, (x, y) in enumerate(self.station_locations):
                ax.annotate(f'{i+1}', (x, y), xytext=(5, 5), 
                           textcoords='offset points', fontsize=9, 
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
        
        # 设置图形属性
        ax.set_xlabel('X 坐标', fontsize=12)
        ax.set_ylabel('Y 坐标', fontsize=12)
        ax.set_title(f'地面观测站从零布设方案\n'
                    f'观测站数量: {len(self.station_locations)}, '
                    f'覆盖半径: {self.sensor_radius}, '
                    f'覆盖率: {len(self.covered_points)/len(self.grid_points)*100:.1f}%', 
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        # 调整坐标轴范围
        minx, miny, maxx, maxy = self.target_area.bounds
        margin = self.sensor_radius * 0.5
        ax.set_xlim(minx - margin, maxx + margin)
        ax.set_ylim(miny - margin, maxy + margin)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"可视化结果已保存到: {save_path}")
        
        plt.show()
    
    def get_coverage_statistics(self) -> dict:
        """
        获取覆盖统计信息
        
        返回:
            包含各种统计信息的字典
        """
        total_points = len(self.grid_points)
        covered_points_count = len(self.covered_points)
        coverage_ratio = covered_points_count / total_points if total_points > 0 else 0
        
        # 计算总覆盖面积（近似）- 基于网格点，避免重叠计算
        covered_area_grid = covered_points_count * (self.grid_resolution ** 2)
        
        # 计算实际几何覆盖面积（精确计算，自动处理重叠）
        actual_covered_area = self._calculate_actual_coverage_area()
        
        total_area = self.target_area.area
        
        return {
            '观测站数量': len(self.station_locations),
            '观测站位置': self.station_locations,
            '总网格点数': total_points,
            '覆盖网格点数': covered_points_count,
            '网格覆盖率': f"{coverage_ratio*100:.2f}%",
            '观测半径': self.sensor_radius,
            '目标区域面积': f"{total_area:.2f}",
            '覆盖面积估算(网格)': f"{covered_area_grid:.2f}",
            '实际覆盖面积(几何)': f"{actual_covered_area:.2f}",
            '实际面积覆盖率': f"{(actual_covered_area/total_area)*100:.2f}%",
            '网格分辨率': self.grid_resolution
        }
    
    def _calculate_actual_coverage_area(self) -> float:
        """
        计算实际覆盖面积（精确几何计算，自动处理重叠）
        
        返回:
            实际覆盖的面积
        """
        if not self.station_locations:
            return 0.0
            
        try:
            # 创建所有观测站的覆盖圆
            coverage_circles = []
            for station in self.station_locations:
                # 创建圆形覆盖区域
                circle = Point(station).buffer(self.sensor_radius)
                # 只考虑与目标区域的交集
                intersection = circle.intersection(self.target_area)
                if not intersection.is_empty:
                    coverage_circles.append(intersection)
            
            if not coverage_circles:
                return 0.0
            
            # 使用shapely的unary_union自动处理重叠并计算总面积
            total_coverage = unary_union(coverage_circles)
            
            # 返回覆盖面积
            if hasattr(total_coverage, 'area'):
                return total_coverage.area
            else:
                return 0.0
                
        except Exception as e:
            print(f"警告：几何面积计算出错: {e}")
            # 如果几何计算失败，回退到网格估算
            return len(self.covered_points) * (self.grid_resolution ** 2)
    
    def export_results(self, filename: str):
        """
        导出结果到文件
        
        参数:
            filename: 输出文件名
        """
        stats = self.get_coverage_statistics()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("地面观测站从零布设结果报告\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("基本信息:\n")
            for key, value in stats.items():
                if key != '观测站位置':
                    f.write(f"  {key}: {value}\n")
            
            f.write(f"\n观测站详细位置:\n")
            for i, pos in enumerate(self.station_locations):
                f.write(f"  观测站 {i+1}: ({pos[0]:.2f}, {pos[1]:.2f})\n")
            
            f.write(f"\n目标区域坐标:\n")
            for i, coord in enumerate(self.target_area_coords):
                f.write(f"  顶点 {i+1}: ({coord[0]:.2f}, {coord[1]:.2f})\n")
        
        print(f"结果已导出到文件: {filename}")


def demo_ground_sensor_from_scratch():
    """演示地面传感器从零布设"""
    print("="*60)
    print("地面传感器从零布设演示")
    print("="*60)
    
    # 示例区域: 矩形
    rectangular_area = [(0, 0), (0, 10), (10, 10), (10, 0)]
    coverage_ratio = 0.8  # 80% 覆盖率
    sensor_radius = 3.0   # 观测半径
    
    print(f"示例: 矩形区域")
    print(f"区域坐标: {rectangular_area}")
    print(f"覆盖要求: {coverage_ratio*100}%")
    print(f"观测半径: {sensor_radius}")
    
    # 创建求解器并求解
    solver = GroundSensorFromScratchSolver(
        target_area_coords=rectangular_area,
        coverage_ratio=coverage_ratio,
        sensor_radius=sensor_radius,
        grid_resolution=0.5
    )
    
    # 求解
    stations, num_stations, actual_coverage = solver.solve()
    
    # 显示结果
    print(f"\n结果:")
    print(f"需要观测站数量: {num_stations}")
    print(f"实际覆盖率: {actual_coverage*100:.2f}%")
    print(f"观测站位置:")
    for i, pos in enumerate(stations):
        print(f"  观测站 {i+1}: ({pos[0]:.2f}, {pos[1]:.2f})")
    
    # 可视化
    solver.visualize(show_grid=False)
    
    # 显示统计信息
    stats = solver.get_coverage_statistics()
    print(f"\n详细统计信息:")
    for key, value in stats.items():
        if key != '观测站位置':
            print(f"  {key}: {value}")
    
    return solver


if __name__ == "__main__":
    demo_ground_sensor_from_scratch()