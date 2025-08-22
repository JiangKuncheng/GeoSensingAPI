"""
地面观测站布设问题 - MCLP (Maximum Coverage Location Problem) 求解器

该模块实现了一个基于贪心算法的地面观测站布设方案，能够在给定的目标区域内
找到最少数量的观测站位置，以满足指定的覆盖比例要求。

主要功能：
1. 目标区域的网格离散化
2. 基于贪心算法的观测站选址
3. 覆盖率计算和验证
4. 可视化展示结果


"""

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely.ops import unary_union
import geopandas as gpd
from typing import List, Tuple, Union
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 用来正常显示负号

class MCLPObservationStationSolver:
    """
    地面观测站布设问题求解器
    
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
        ax.set_title(f'地面观测站布设方案\n'
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
    
    def get_detailed_coverage_analysis(self) -> dict:
        """
        获取详细的覆盖分析，包括重叠分析
        
        返回:
            详细的覆盖分析结果
        """
        if not self.station_locations:
            return {'error': '没有观测站数据'}
        
        try:
            # 计算每个观测站的独立覆盖面积
            individual_areas = []
            individual_coverage_in_target = []
            
            for i, station in enumerate(self.station_locations):
                circle = Point(station).buffer(self.sensor_radius)
                # 观测站的总覆盖面积
                total_circle_area = circle.area
                individual_areas.append(total_circle_area)
                
                # 在目标区域内的覆盖面积
                intersection = circle.intersection(self.target_area)
                area_in_target = intersection.area if hasattr(intersection, 'area') else 0.0
                individual_coverage_in_target.append(area_in_target)
            
            # 计算总的理论覆盖面积（如果没有重叠）
            total_theoretical_area = sum(individual_coverage_in_target)
            
            # 计算实际覆盖面积（处理重叠后）
            actual_coverage_area = self._calculate_actual_coverage_area()
            
            # 计算重叠面积
            overlap_area = total_theoretical_area - actual_coverage_area
            overlap_percentage = (overlap_area / total_theoretical_area * 100) if total_theoretical_area > 0 else 0
            
            return {
                '观测站数量': len(self.station_locations),
                '单站覆盖面积': [f"{area:.2f}" for area in individual_areas],
                '单站目标区域内覆盖': [f"{area:.2f}" for area in individual_coverage_in_target],
                '理论总覆盖面积': f"{total_theoretical_area:.2f}",
                '实际总覆盖面积': f"{actual_coverage_area:.2f}",
                '重叠面积': f"{overlap_area:.2f}",
                '重叠比例': f"{overlap_percentage:.2f}%",
                '覆盖效率': f"{(actual_coverage_area/total_theoretical_area)*100:.2f}%" if total_theoretical_area > 0 else "0%"
            }
            
        except Exception as e:
            return {'error': f'覆盖分析计算出错: {e}'}
    
    def export_results(self, filename: str):
        """
        导出结果到文件
        
        参数:
            filename: 输出文件名
        """
        stats = self.get_coverage_statistics()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("地面观测站布设结果报告\n")
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

    def optimize_existing_stations(self, existing_stations: List[Tuple[float, float]], 
                                 target_coverage_ratio: float = None,
                                 max_iterations: int = 100) -> Tuple[List[Tuple[float, float]], float, dict]:
        """
        优化已有传感器布设方案（不增加传感器数量）
        
        参数:
            existing_stations: 现有传感器位置列表 [(x1,y1), (x2,y2), ...]
            target_coverage_ratio: 目标覆盖率，如果为None则使用初始化时的覆盖率
            max_iterations: 最大优化迭代次数
            
        返回:
            优化后的传感器位置, 实际覆盖率, 优化统计信息
        """
        if not existing_stations:
            raise ValueError("传感器位置列表不能为空")
        
        if target_coverage_ratio is None:
            target_coverage_ratio = self.coverage_ratio
        
        print(f"开始优化现有传感器布设方案...")
        print(f"传感器数量: {len(existing_stations)} (固定不变)")
        print(f"目标覆盖率: {target_coverage_ratio*100:.1f}%")
        print(f"观测半径: {self.sensor_radius}")
        
        # 保存原始配置
        original_coverage_ratio = self.coverage_ratio
        self.coverage_ratio = target_coverage_ratio
        
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
            if current_coverage >= target_coverage_ratio:
                print(f"已达到目标覆盖率 {target_coverage_ratio*100:.1f}%，优化结束")
                break
        
        # 恢复原始配置
        self.coverage_ratio = original_coverage_ratio
        
        # 准备优化统计信息
        optimization_stats = {
            '初始覆盖率': f"{initial_coverage*100:.2f}%",
            '优化后覆盖率': f"{best_coverage*100:.2f}%",
            '覆盖率提升': f"{(best_coverage-initial_coverage)*100:.2f}%",
            '传感器数量': len(existing_stations),
            '目标覆盖率': f"{target_coverage_ratio*100:.1f}%",
            '是否达到目标': "是" if best_coverage >= target_coverage_ratio else "否",
            '优化迭代次数': len(optimization_history),
            '优化历史': optimization_history
        }
        
        print(f"\n优化完成!")
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"优化后覆盖率: {best_coverage*100:.2f}%")
        print(f"覆盖率提升: {(best_coverage-initial_coverage)*100:.2f}%")
        
        return best_stations, best_coverage, optimization_stats
    
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
    
    def compare_station_layouts(self, original_stations: List[Tuple[float, float]], 
                              optimized_stations: List[Tuple[float, float]]) -> dict:
        """
        比较原始和优化后的传感器布局
        
        参数:
            original_stations: 原始传感器位置
            optimized_stations: 优化后传感器位置
            
        返回:
            详细比较结果
        """
        # 临时保存当前观测站位置
        temp_stations = self.station_locations.copy()
        temp_covered = self.covered_points.copy()
        
        # 评估原始布局
        self.station_locations = original_stations
        self.covered_points = set()
        for station_pos in original_stations:
            covered = self._calculate_coverage_for_position(station_pos)
            self.covered_points.update(covered)
        
        original_stats = self.get_coverage_statistics()
        original_detailed = self.get_detailed_coverage_analysis()
        
        # 评估优化后布局
        self.station_locations = optimized_stations
        self.covered_points = set()
        for station_pos in optimized_stations:
            covered = self._calculate_coverage_for_position(station_pos)
            self.covered_points.update(covered)
            
        optimized_stats = self.get_coverage_statistics()
        optimized_detailed = self.get_detailed_coverage_analysis()
        
        # 恢复原始状态
        self.station_locations = temp_stations
        self.covered_points = temp_covered
        
        # 计算改进幅度
        original_coverage = float(original_stats['网格覆盖率'].replace('%', ''))
        optimized_coverage = float(optimized_stats['网格覆盖率'].replace('%', ''))
        improvement = optimized_coverage - original_coverage
        
        return {
            '原始方案': {
                '覆盖率': original_stats['网格覆盖率'],
                '覆盖面积': original_stats['实际覆盖面积(几何)'],
                '重叠比例': original_detailed.get('重叠比例', 'N/A') if 'error' not in original_detailed else 'N/A'
            },
            '优化方案': {
                '覆盖率': optimized_stats['网格覆盖率'],
                '覆盖面积': optimized_stats['实际覆盖面积(几何)'],
                '重叠比例': optimized_detailed.get('重叠比例', 'N/A') if 'error' not in optimized_detailed else 'N/A'
            },
            '改进效果': {
                '覆盖率提升': f"{improvement:.2f}%",
                '是否有改进': "是" if improvement > 0 else "否"
            }
        }

    def optimize_with_additional_stations(self, existing_stations: List[Tuple[float, float]], 
                                        target_coverage_ratio: float,
                                        max_additional_stations: int = 10) -> Tuple[List[Tuple[float, float]], float, dict]:
        """
        通过新增传感器优化覆盖率（当现有传感器无法满足目标时使用）
        
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
        
        # 首先尝试优化现有传感器位置
        print(f"\n第一步：优化现有传感器位置")
        try:
            optimized_existing, coverage_after_position_opt, _ = self.optimize_existing_stations(
                existing_stations=existing_stations,
                target_coverage_ratio=target_coverage_ratio,
                max_iterations=30
            )
            print(f"位置优化后覆盖率: {coverage_after_position_opt*100:.2f}%")
        except Exception as e:
            print(f"位置优化失败，使用原始位置: {e}")
            optimized_existing = existing_stations.copy()
            coverage_after_position_opt = self._evaluate_station_layout(existing_stations)
        
        # 如果已经满足目标，直接返回
        if coverage_after_position_opt >= target_coverage_ratio:
            print(f"仅通过位置优化已达到目标覆盖率")
            return optimized_existing, coverage_after_position_opt, {
                '初始覆盖率': f"{self._evaluate_station_layout(existing_stations)*100:.2f}%",
                '位置优化后覆盖率': f"{coverage_after_position_opt*100:.2f}%",
                '最终覆盖率': f"{coverage_after_position_opt*100:.2f}%",
                '原有传感器数量': len(existing_stations),
                '新增传感器数量': 0,
                '最终传感器数量': len(optimized_existing),
                '是否达到目标': "是",
                '优化策略': "仅位置优化"
            }
        
        # 第二步：贪心添加新传感器
        print(f"\n第二步：贪心添加新传感器")
        current_stations = optimized_existing.copy()
        current_coverage = coverage_after_position_opt
        
        # 获取候选位置
        candidate_positions = self._get_candidate_positions()
        
        added_stations = []
        optimization_history = []
        
        for additional_count in range(max_additional_stations):
            if current_coverage >= target_coverage_ratio:
                print(f"已达到目标覆盖率，停止添加传感器")
                break
            
            best_position = None
            best_new_coverage = current_coverage
            
            # 尝试每个候选位置
            for candidate_pos in candidate_positions:
                # 避免与现有传感器位置重复
                if self._is_too_close_to_existing(candidate_pos, current_stations):
                    continue
                
                # 临时添加候选传感器
                temp_stations = current_stations + [candidate_pos]
                temp_coverage = self._evaluate_station_layout(temp_stations)
                
                # 如果找到更好的位置
                if temp_coverage > best_new_coverage:
                    best_new_coverage = temp_coverage
                    best_position = candidate_pos
            
            # 如果找到改进的位置
            if best_position is not None:
                current_stations.append(best_position)
                added_stations.append(best_position)
                current_coverage = best_new_coverage
                
                print(f"添加传感器 {additional_count + 1}: {best_position}, "
                      f"覆盖率: {current_coverage*100:.2f}%")
                
                optimization_history.append({
                    'added_station': best_position,
                    'coverage': current_coverage,
                    'total_stations': len(current_stations)
                })
            else:
                print(f"无法找到有效的新增位置，停止添加")
                break
        
        # 第三步：对所有传感器（包括新增的）进行最终位置优化
        if added_stations:
            print(f"\n第三步：对所有传感器进行最终位置优化")
            try:
                final_stations, final_coverage, _ = self.optimize_existing_stations(
                    existing_stations=current_stations,
                    target_coverage_ratio=target_coverage_ratio,
                    max_iterations=20
                )
                print(f"最终优化后覆盖率: {final_coverage*100:.2f}%")
            except Exception as e:
                print(f"最终优化失败，使用当前位置: {e}")
                final_stations = current_stations
                final_coverage = current_coverage
        else:
            final_stations = current_stations
            final_coverage = current_coverage
        
        # 准备统计信息
        initial_coverage = self._evaluate_station_layout(existing_stations)
        optimization_stats = {
            '初始覆盖率': f"{initial_coverage*100:.2f}%",
            '位置优化后覆盖率': f"{coverage_after_position_opt*100:.2f}%",
            '最终覆盖率': f"{final_coverage*100:.2f}%",
            '总覆盖率提升': f"{(final_coverage-initial_coverage)*100:.2f}%",
            '原有传感器数量': len(existing_stations),
            '新增传感器数量': len(added_stations),
            '最终传感器数量': len(final_stations),
            '目标覆盖率': f"{target_coverage_ratio*100:.1f}%",
            '是否达到目标': "是" if final_coverage >= target_coverage_ratio else "否",
            '新增传感器位置': added_stations,
            '优化历史': optimization_history,
            '优化策略': "位置优化 + 新增传感器"
        }
        
        print(f"\n优化完成!")
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"最终覆盖率: {final_coverage*100:.2f}%")
        print(f"新增传感器数量: {len(added_stations)}")
        print(f"总传感器数量: {len(final_stations)}")
        
        return final_stations, final_coverage, optimization_stats
    
    def _is_too_close_to_existing(self, candidate_pos: Tuple[float, float], 
                                existing_stations: List[Tuple[float, float]], 
                                min_distance: float = None) -> bool:
        """
        检查候选位置是否与现有传感器太近
        
        参数:
            candidate_pos: 候选位置
            existing_stations: 现有传感器位置列表
            min_distance: 最小距离，默认为观测半径的一半
            
        返回:
            如果太近返回True，否则返回False
        """
        if min_distance is None:
            min_distance = self.sensor_radius * 0.5  # 默认为观测半径的一半
        
        candidate_point = Point(candidate_pos)
        
        for station_pos in existing_stations:
            station_point = Point(station_pos)
            if candidate_point.distance(station_point) < min_distance:
                return True
        
        return False
    
    def smart_station_optimization(self, existing_stations: List[Tuple[float, float]], 
                                 target_coverage_ratio: float,
                                 max_additional_stations: int = 5) -> Tuple[List[Tuple[float, float]], float, dict]:
        """
        智能传感器优化：自动选择最佳优化策略
        
        参数:
            existing_stations: 现有传感器位置列表
            target_coverage_ratio: 目标覆盖率
            max_additional_stations: 最大可新增传感器数量
            
        返回:
            最优传感器位置列表, 实际覆盖率, 优化统计信息
        """
        print(f"智能传感器优化开始...")
        print(f"现有传感器: {len(existing_stations)} 个")
        print(f"目标覆盖率: {target_coverage_ratio*100:.1f}%")
        
        # 评估初始状态
        initial_coverage = self._evaluate_station_layout(existing_stations)
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        
        # 策略1：仅优化位置
        print(f"\n尝试策略1：仅优化传感器位置")
        optimized_positions, position_coverage, position_stats = self.optimize_existing_stations(
            existing_stations=existing_stations,
            target_coverage_ratio=target_coverage_ratio,
            max_iterations=30
        )
        
        # 如果位置优化就能满足要求
        if position_coverage >= target_coverage_ratio:
            print(f"策略1成功：仅通过位置优化达到目标")
            return optimized_positions, position_coverage, {
                **position_stats,
                '选用策略': "仅位置优化",
                '新增传感器数量': 0
            }
        
        # 策略2：位置优化 + 新增传感器
        print(f"\n策略1未达标，尝试策略2：位置优化 + 新增传感器")
        final_stations, final_coverage, addition_stats = self.optimize_with_additional_stations(
            existing_stations=existing_stations,
            target_coverage_ratio=target_coverage_ratio,
            max_additional_stations=max_additional_stations
        )
        
        return final_stations, final_coverage, {
            **addition_stats,
            '选用策略': "位置优化 + 新增传感器",
            '位置优化效果': f"从 {initial_coverage*100:.2f}% 提升到 {position_coverage*100:.2f}%"
        }


def main():
    """主函数，展示使用示例"""
    # 示例1: 矩形区域
    print("=" * 60)
    print("地面观测站布设问题求解示例")
    print("=" * 60)
    
    # 示例区域: 矩形
    rectangular_area = [(0, 0), (0, 10), (10, 10), (10, 0)]
    coverage_ratio = 0.8  # 80% 覆盖率
    sensor_radius = 3.0   # 观测半径
    
    print(f"\n示例1: 矩形区域")
    print(f"区域坐标: {rectangular_area}")
    print(f"覆盖要求: {coverage_ratio*100}%")
    print(f"观测半径: {sensor_radius}")
    
    # 创建求解器并求解
    solver = MCLPObservationStationSolver(
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
    
    # 导出结果
    solver.export_results("deploy/observation_stations_result.txt")
    
    # 显示统计信息
    stats = solver.get_coverage_statistics()
    print(f"\n详细统计信息:")
    for key, value in stats.items():
        if key != '观测站位置':
            print(f"  {key}: {value}")
    
    # 显示重叠分析
    overlap_analysis = solver.get_detailed_coverage_analysis()
    print(f"\n重叠分析:")
    for key, value in overlap_analysis.items():
        if key not in ['单站覆盖面积', '单站目标区域内覆盖']:
            print(f"  {key}: {value}")
        elif key == '单站目标区域内覆盖':
            print(f"  各观测站目标区域内覆盖面积: {', '.join(value)}")


if __name__ == "__main__":
    main()