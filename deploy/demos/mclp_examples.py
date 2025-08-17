"""
地面观测站布设问题高级示例
包含多种复杂场景的演示和测试


"""

from mclp_observation_station import MCLPObservationStationSolver
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.dont_write_bytecode = True

def example_irregular_polygon():
    """示例2: 不规则多边形区域"""
    print("\n" + "="*50)
    print("示例2: 不规则多边形区域")
    print("="*50)
    
    # 创建一个不规则多边形（模拟湖泊或山区）
    irregular_area = [
        (0, 0), (3, 1), (6, 0), (8, 3), (7, 6), 
        (5, 8), (3, 7), (1, 8), (-1, 5), (0, 2)
    ]
    
    coverage_ratio = 0.75  # 75% 覆盖率
    sensor_radius = 2.5    # 观测半径
    
    print(f"区域类型: 不规则多边形")
    print(f"覆盖要求: {coverage_ratio*100}%")
    print(f"观测半径: {sensor_radius}")
    
    solver = MCLPObservationStationSolver(
        target_area_coords=irregular_area,
        coverage_ratio=coverage_ratio,
        sensor_radius=sensor_radius,
        grid_resolution=0.3  # 更细的网格
    )
    
    stations, num_stations, actual_coverage = solver.solve()
    
    print(f"\n结果:")
    print(f"需要观测站数量: {num_stations}")
    print(f"实际覆盖率: {actual_coverage*100:.2f}%")
    
    # 可视化
    solver.visualize(show_grid=False)
    
    return solver


def example_coastal_area():
    """示例3: 海岸线监测区域"""
    print("\n" + "="*50)
    print("示例3: 海岸线监测区域")
    print("="*50)
    
    # 模拟海岸线区域（狭长地带）
    coastal_area = [
        (0, 0), (15, 2), (20, 1), (25, 3), (30, 2),
        (35, 4), (40, 3), (40, 6), (35, 7), (30, 5),
        (25, 6), (20, 4), (15, 5), (0, 3)
    ]
    
    coverage_ratio = 0.85  # 85% 覆盖率（海岸线需要高覆盖）
    sensor_radius = 4.0    # 较大的观测半径
    
    print(f"区域类型: 海岸线监测区域")
    print(f"覆盖要求: {coverage_ratio*100}%")
    print(f"观测半径: {sensor_radius}")
    
    solver = MCLPObservationStationSolver(
        target_area_coords=coastal_area,
        coverage_ratio=coverage_ratio,
        sensor_radius=sensor_radius,
        grid_resolution=0.4
    )
    
    stations, num_stations, actual_coverage = solver.solve()
    
    print(f"\n结果:")
    print(f"需要观测站数量: {num_stations}")
    print(f"实际覆盖率: {actual_coverage*100:.2f}%")
    
    # 可视化
    solver.visualize(show_grid=False)
    
    return solver


def example_urban_area():
    """示例4: 城市区域监测"""
    print("\n" + "="*50)
    print("示例4: 城市区域监测")
    print("="*50)
    
    # 模拟城市区域（正方形但有缺口）
    urban_area = [
        (0, 0), (12, 0), (12, 4), (8, 4), (8, 8),
        (12, 8), (12, 12), (0, 12), (0, 8), (4, 8),
        (4, 4), (0, 4)
    ]
    
    coverage_ratio = 0.90  # 90% 覆盖率（城市需要高覆盖）
    sensor_radius = 2.8    # 中等观测半径
    
    print(f"区域类型: 城市监测区域")
    print(f"覆盖要求: {coverage_ratio*100}%")
    print(f"观测半径: {sensor_radius}")
    
    solver = MCLPObservationStationSolver(
        target_area_coords=urban_area,
        coverage_ratio=coverage_ratio,
        sensor_radius=sensor_radius,
        grid_resolution=0.25  # 高精度网格
    )
    
    stations, num_stations, actual_coverage = solver.solve()
    
    print(f"\n结果:")
    print(f"需要观测站数量: {num_stations}")
    print(f"实际覆盖率: {actual_coverage*100:.2f}%")
    
    # 可视化
    solver.visualize(show_grid=True)  # 显示网格点
    
    return solver


def sensitivity_analysis():
    """敏感性分析：不同参数对结果的影响"""
    print("\n" + "="*50)
    print("敏感性分析")
    print("="*50)
    
    # 固定区域
    base_area = [(0, 0), (0, 10), (10, 10), (10, 0)]
    
    # 测试不同的观测半径
    radii = [2.0, 2.5, 3.0, 3.5, 4.0]
    coverage_ratio = 0.8
    
    results = []
    
    print("测试不同观测半径的影响:")
    print("半径\t观测站数量\t实际覆盖率")
    print("-" * 35)
    
    for radius in radii:
        solver = MCLPObservationStationSolver(
            target_area_coords=base_area,
            coverage_ratio=coverage_ratio,
            sensor_radius=radius,
            grid_resolution=0.4
        )
        
        stations, num_stations, actual_coverage = solver.solve()
        results.append((radius, num_stations, actual_coverage))
        
        print(f"{radius:.1f}\t{num_stations}\t\t{actual_coverage*100:.1f}%")
    
    # 绘制敏感性分析图
    radii_vals, station_counts, coverage_vals = zip(*results)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    
    # 观测站数量 vs 半径
    ax1.plot(radii_vals, station_counts, 'bo-', linewidth=2, markersize=8)
    ax1.set_xlabel('观测半径', fontsize=12)
    ax1.set_ylabel('所需观测站数量', fontsize=12)
    ax1.set_title('观测站数量 vs 观测半径', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 覆盖率 vs 半径
    coverage_percentages = [c*100 for c in coverage_vals]
    ax2.plot(radii_vals, coverage_percentages, 'ro-', linewidth=2, markersize=8)
    ax2.axhline(y=80, color='g', linestyle='--', alpha=0.7, label='目标覆盖率 80%')
    ax2.set_xlabel('观测半径', fontsize=12)
    ax2.set_ylabel('实际覆盖率 (%)', fontsize=12)
    ax2.set_title('实际覆盖率 vs 观测半径', fontsize=12, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return results


def compare_grid_resolutions():
    """比较不同网格分辨率的影响"""
    print("\n" + "="*50)
    print("网格分辨率比较分析")
    print("="*50)
    
    base_area = [(0, 0), (0, 8), (8, 8), (8, 0)]
    coverage_ratio = 0.8
    sensor_radius = 2.5
    
    resolutions = [0.2, 0.4, 0.6, 0.8, 1.0]
    
    print("网格分辨率\t网格点数\t观测站数量\t覆盖率\t计算时间")
    print("-" * 60)
    
    import time
    
    for resolution in resolutions:
        start_time = time.time()
        
        solver = MCLPObservationStationSolver(
            target_area_coords=base_area,
            coverage_ratio=coverage_ratio,
            sensor_radius=sensor_radius,
            grid_resolution=resolution
        )
        
        stations, num_stations, actual_coverage = solver.solve()
        
        end_time = time.time()
        compute_time = end_time - start_time
        
        print(f"{resolution:.1f}\t\t{len(solver.grid_points)}\t\t{num_stations}\t\t"
              f"{actual_coverage*100:.1f}%\t{compute_time:.2f}s")


def main():
    """运行所有示例"""
    print("地面观测站布设问题 - 高级示例集")
    print("="*60)
    
    # 运行各种示例
    example_irregular_polygon()
    example_coastal_area() 
    example_urban_area()
    
    # 运行分析
    sensitivity_analysis()
    compare_grid_resolutions()
    
    print("\n" + "="*60)
    print("所有示例运行完成！")
    print("="*60)


if __name__ == "__main__":
    main()