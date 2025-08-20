"""
传感器布设优化演示
演示如何优化已有的传感器布设方案，在不增加传感器数量的情况下提高覆盖率
"""

from mclp_observation_station import MCLPObservationStationSolver
import matplotlib.pyplot as plt
import numpy as np

def demo_station_optimization():
    """演示传感器位置优化功能"""
    print("="*60)
    print("传感器布设优化演示")
    print("="*60)
    
    # 定义目标区域
    area_coords = [(0, 0), (0, 12), (12, 12), (12, 0)]
    sensor_radius = 3.5
    target_coverage = 0.8  # 目标80%覆盖率
    
    # 创建求解器
    solver = MCLPObservationStationSolver(
        target_area_coords=area_coords,
        coverage_ratio=target_coverage,
        sensor_radius=sensor_radius,
        grid_resolution=0.4
    )
    
    print(f"目标区域: 12x12 矩形")
    print(f"观测半径: {sensor_radius}")
    print(f"目标覆盖率: {target_coverage*100}%")
    
    # 模拟用户的非最优布设方案
    user_stations = [
        (2, 2),    # 用户放置的第1个传感器
        (6, 3),    # 用户放置的第2个传感器  
        (10, 7),   # 用户放置的第3个传感器
        (4, 8),    # 用户放置的第4个传感器
        (8, 10)    # 用户放置的第5个传感器
    ]
    
    print(f"\n用户当前传感器布设:")
    for i, pos in enumerate(user_stations):
        print(f"  传感器 {i+1}: {pos}")
    
    # 评估用户方案的初始覆盖率
    initial_coverage = solver._evaluate_station_layout(user_stations)
    print(f"用户方案初始覆盖率: {initial_coverage*100:.2f}%")
    
    # 优化传感器布设
    print(f"\n开始优化...")
    optimized_stations, final_coverage, optimization_stats = solver.optimize_existing_stations(
        existing_stations=user_stations,
        target_coverage_ratio=target_coverage,
        max_iterations=50
    )
    
    print(f"\n优化后传感器布设:")
    for i, pos in enumerate(optimized_stations):
        print(f"  传感器 {i+1}: ({pos[0]:.2f}, {pos[1]:.2f})")
    
    # 显示优化统计
    print(f"\n优化统计:")
    for key, value in optimization_stats.items():
        if key != '优化历史':
            print(f"  {key}: {value}")
    
    # 比较原始和优化方案
    comparison = solver.compare_station_layouts(user_stations, optimized_stations)
    print(f"\n详细比较:")
    for category, data in comparison.items():
        print(f"  {category}:")
        for key, value in data.items():
            print(f"    {key}: {value}")
    
    # 可视化比较
    visualize_optimization_comparison(solver, user_stations, optimized_stations, 
                                    initial_coverage, final_coverage)
    
    return solver, user_stations, optimized_stations, optimization_stats

def demo_different_target_coverage():
    """演示不同目标覆盖率的优化效果"""
    print("\n" + "="*60)
    print("不同目标覆盖率优化比较")
    print("="*60)
    
    area_coords = [(0, 0), (0, 10), (10, 10), (10, 0)]
    sensor_radius = 2.8
    
    # 固定的用户传感器布设（较差的布局）
    user_stations = [
        (1, 1), (3, 2), (7, 1), (2, 6), (8, 8), (5, 9)
    ]
    
    # 测试不同的目标覆盖率
    target_coverages = [0.6, 0.7, 0.8, 0.9]
    results = []
    
    for target in target_coverages:
        print(f"\n--- 目标覆盖率: {target*100}% ---")
        
        solver = MCLPObservationStationSolver(
            target_area_coords=area_coords,
            coverage_ratio=target,
            sensor_radius=sensor_radius,
            grid_resolution=0.3
        )
        
        initial_coverage = solver._evaluate_station_layout(user_stations)
        
        optimized_stations, final_coverage, stats = solver.optimize_existing_stations(
            existing_stations=user_stations,
            target_coverage_ratio=target,
            max_iterations=30
        )
        
        improvement = final_coverage - initial_coverage
        achieved_target = final_coverage >= target
        
        results.append({
            'target': target,
            'initial': initial_coverage,
            'final': final_coverage,
            'improvement': improvement,
            'achieved': achieved_target,
            'iterations': stats['优化迭代次数']
        })
        
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"优化后覆盖率: {final_coverage*100:.2f}%")
        print(f"改进幅度: {improvement*100:.2f}%")
        print(f"达到目标: {'是' if achieved_target else '否'}")
    
    # 绘制结果比较图
    plot_target_coverage_comparison(results)
    
    return results

def visualize_optimization_comparison(solver, original_stations, optimized_stations, 
                                    initial_coverage, final_coverage):
    """可视化优化前后的对比"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # 绘制原始方案
    plot_station_layout(ax1, solver, original_stations, 
                       f"原始方案 (覆盖率: {initial_coverage*100:.1f}%)")
    
    # 绘制优化方案
    plot_station_layout(ax2, solver, optimized_stations, 
                       f"优化方案 (覆盖率: {final_coverage*100:.1f}%)")
    
    plt.tight_layout()
    plt.show()

def plot_station_layout(ax, solver, stations, title):
    """绘制传感器布局"""
    # 绘制目标区域
    x_coords, y_coords = zip(*solver.target_area_coords)
    ax.plot(list(x_coords) + [x_coords[0]], 
            list(y_coords) + [y_coords[0]], 
            'b-', linewidth=2, label='目标区域')
    ax.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
    
    # 绘制传感器覆盖范围
    for i, station in enumerate(stations):
        circle = plt.Circle(station, solver.sensor_radius, 
                          fill=False, color='red', alpha=0.6, linewidth=1.5)
        ax.add_patch(circle)
        
        # 填充覆盖区域
        circle_fill = plt.Circle(station, solver.sensor_radius, 
                               fill=True, color='red', alpha=0.1)
        ax.add_patch(circle_fill)
    
    # 绘制传感器位置
    if stations:
        station_x, station_y = zip(*stations)
        ax.scatter(station_x, station_y, c='red', s=100, 
                  marker='s', label=f'传感器 ({len(stations)}个)', 
                  edgecolors='black', linewidth=1, zorder=5)
        
        # 标注传感器编号
        for i, (x, y) in enumerate(stations):
            ax.annotate(f'{i+1}', (x, y), xytext=(5, 5), 
                       textcoords='offset points', fontsize=9,
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    ax.set_xlabel('X 坐标')
    ax.set_ylabel('Y 坐标')
    ax.set_title(title, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # 设置坐标轴范围
    minx, miny, maxx, maxy = solver.target_area.bounds
    margin = solver.sensor_radius * 0.5
    ax.set_xlim(minx - margin, maxx + margin)
    ax.set_ylim(miny - margin, maxy + margin)

def plot_target_coverage_comparison(results):
    """绘制不同目标覆盖率的比较图"""
    targets = [r['target']*100 for r in results]
    initials = [r['initial']*100 for r in results]
    finals = [r['final']*100 for r in results]
    improvements = [r['improvement']*100 for r in results]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 覆盖率对比图
    x = np.arange(len(targets))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, initials, width, label='初始覆盖率', alpha=0.8, color='lightcoral')
    bars2 = ax1.bar(x + width/2, finals, width, label='优化后覆盖率', alpha=0.8, color='lightgreen')
    
    # 添加目标线
    ax1.plot(x, targets, 'r--', marker='o', label='目标覆盖率', linewidth=2)
    
    ax1.set_xlabel('目标覆盖率设置')
    ax1.set_ylabel('覆盖率 (%)')
    ax1.set_title('不同目标覆盖率下的优化效果', fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{t:.0f}%' for t in targets])
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 改进幅度图
    bars3 = ax2.bar(range(len(improvements)), improvements, color='gold', alpha=0.8)
    ax2.set_xlabel('目标覆盖率设置')
    ax2.set_ylabel('覆盖率改进 (%)')
    ax2.set_title('优化改进幅度', fontweight='bold')
    ax2.set_xticks(range(len(targets)))
    ax2.set_xticklabels([f'{t:.0f}%' for t in targets])
    ax2.grid(True, alpha=0.3)
    
    # 在柱子上添加数值标签
    for bar, improvement in zip(bars3, improvements):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{improvement:.1f}%', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.show()

def demo_iterative_optimization():
    """演示迭代优化过程"""
    print("\n" + "="*60)
    print("迭代优化过程演示")
    print("="*60)
    
    area_coords = [(0, 0), (0, 8), (8, 8), (8, 0)]
    
    # 故意设置一个很差的初始布局
    poor_stations = [(1, 1), (2, 1), (3, 1), (7, 7)]  # 聚集在一起
    
    solver = MCLPObservationStationSolver(
        target_area_coords=area_coords,
        coverage_ratio=0.75,
        sensor_radius=2.5,
        grid_resolution=0.3
    )
    
    print("初始布局（故意设置为较差布局）:")
    for i, pos in enumerate(poor_stations):
        print(f"  传感器 {i+1}: {pos}")
    
    initial_coverage = solver._evaluate_station_layout(poor_stations)
    print(f"初始覆盖率: {initial_coverage*100:.2f}%")
    
    # 执行优化并获取详细历史
    optimized_stations, final_coverage, stats = solver.optimize_existing_stations(
        existing_stations=poor_stations,
        target_coverage_ratio=0.75,
        max_iterations=20
    )
    
    # 显示优化历史
    print(f"\n优化历史:")
    for step in stats['优化历史'][:5]:  # 只显示前5步
        print(f"  迭代 {step['iteration']}: 覆盖率 {step['coverage']*100:.2f}%")
    
    print(f"\n最终结果:")
    print(f"最终覆盖率: {final_coverage*100:.2f}%")
    print(f"总改进幅度: {(final_coverage-initial_coverage)*100:.2f}%")
    
    return solver, poor_stations, optimized_stations

def demo_additional_stations_optimization():
    """演示新增传感器优化功能"""
    print("\n" + "="*60)
    print("新增传感器优化演示")
    print("="*60)
    
    # 设置一个较大的区域和较高的目标覆盖率
    area_coords = [(0, 0), (0, 15), (15, 15), (15, 0)]
    sensor_radius = 3.0
    target_coverage = 0.85  # 高目标覆盖率85%
    
    # 创建求解器
    solver = MCLPObservationStationSolver(
        target_area_coords=area_coords,
        coverage_ratio=target_coverage,
        sensor_radius=sensor_radius,
        grid_resolution=0.4
    )
    
    print(f"目标区域: 15x15 矩形")
    print(f"观测半径: {sensor_radius}")
    print(f"目标覆盖率: {target_coverage*100}% (较高要求)")
    
    # 用户当前的传感器布设（数量不足）
    insufficient_stations = [
        (3, 3), (7, 4), (11, 7), (5, 10)
    ]
    
    print(f"\n用户当前传感器布设（数量可能不足）:")
    for i, pos in enumerate(insufficient_stations):
        print(f"  传感器 {i+1}: {pos}")
    
    initial_coverage = solver._evaluate_station_layout(insufficient_stations)
    print(f"初始覆盖率: {initial_coverage*100:.2f}%")
    
    if initial_coverage >= target_coverage:
        print(f"当前传感器已满足目标，无需新增")
        return
    
    print(f"当前覆盖率不足，需要优化方案")
    
    # 新增传感器优化
    print(f"\n开始新增传感器优化...")
    optimized_stations, final_coverage, stats = solver.optimize_with_additional_stations(
        existing_stations=insufficient_stations,
        target_coverage_ratio=target_coverage,
        max_additional_stations=8
    )
    
    print(f"\n优化结果:")
    print(f"原有传感器: {stats['原有传感器数量']}")
    print(f"新增传感器: {stats['新增传感器数量']}")
    print(f"最终传感器数量: {stats['最终传感器数量']}")
    print(f"最终覆盖率: {stats['最终覆盖率']}")
    print(f"是否达到目标: {stats['是否达到目标']}")
    
    # 显示新增传感器的位置
    new_stations = stats['新增传感器位置']
    if new_stations:
        print(f"\n新增传感器位置:")
        for i, pos in enumerate(new_stations):
            print(f"  新增传感器 {i+1}: ({pos[0]:.2f}, {pos[1]:.2f})")
    
    # 可视化结果
    visualize_additional_stations_comparison(solver, insufficient_stations, optimized_stations,
                                           new_stations, initial_coverage, final_coverage)
    
    return solver, insufficient_stations, optimized_stations, stats

def demo_smart_optimization():
    """演示智能优化策略"""
    print("\n" + "="*60)
    print("智能优化策略演示")
    print("="*60)
    
    scenarios = [
        {
            "name": "场景1：位置优化即可满足",
            "area": [(0, 0), (0, 8), (8, 8), (8, 0)],
            "stations": [(2, 2), (6, 6), (2, 6), (6, 2)],  # 位置不佳但数量足够
            "target": 0.75,
            "radius": 2.8
        },
        {
            "name": "场景2：需要新增传感器",
            "area": [(0, 0), (0, 12), (12, 12), (12, 0)],
            "stations": [(3, 3), (9, 9)],  # 数量明显不足
            "target": 0.8,
            "radius": 3.0
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"区域大小: {max([p[0] for p in scenario['area']])}x{max([p[1] for p in scenario['area']])}")
        print(f"初始传感器数量: {len(scenario['stations'])}")
        print(f"目标覆盖率: {scenario['target']*100}%")
        
        solver = MCLPObservationStationSolver(
            target_area_coords=scenario['area'],
            coverage_ratio=scenario['target'],
            sensor_radius=scenario['radius'],
            grid_resolution=0.3
        )
        
        initial_coverage = solver._evaluate_station_layout(scenario['stations'])
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        
        # 使用智能优化策略
        optimized_stations, final_coverage, smart_stats = solver.smart_station_optimization(
            existing_stations=scenario['stations'],
            target_coverage_ratio=scenario['target'],
            max_additional_stations=5
        )
        
        print(f"选用策略: {smart_stats['选用策略']}")
        print(f"最终覆盖率: {final_coverage*100:.2f}%")
        if '新增传感器数量' in smart_stats:
            print(f"新增传感器: {smart_stats['新增传感器数量']} 个")
        print(f"达到目标: {smart_stats.get('是否达到目标', 'N/A')}")

def demo_cost_effectiveness_analysis():
    """演示成本效益分析"""
    print("\n" + "="*60)
    print("成本效益分析演示")
    print("="*60)
    
    area_coords = [(0, 0), (0, 10), (10, 10), (10, 0)]
    base_stations = [(2, 2), (8, 8)]  # 基础配置
    sensor_radius = 2.5
    
    # 测试不同目标覆盖率的成本
    target_coverages = [0.6, 0.7, 0.8, 0.9]
    cost_analysis = []
    
    print(f"基础传感器配置: {len(base_stations)} 个")
    print(f"观测半径: {sensor_radius}")
    
    for target in target_coverages:
        print(f"\n--- 目标覆盖率: {target*100}% ---")
        
        solver = MCLPObservationStationSolver(
            target_area_coords=area_coords,
            coverage_ratio=target,
            sensor_radius=sensor_radius,
            grid_resolution=0.3
        )
        
        initial_coverage = solver._evaluate_station_layout(base_stations)
        
        # 尝试智能优化
        optimized_stations, final_coverage, stats = solver.smart_station_optimization(
            existing_stations=base_stations,
            target_coverage_ratio=target,
            max_additional_stations=6
        )
        
        additional_sensors = stats.get('新增传感器数量', 0)
        achieved = final_coverage >= target
        
        cost_analysis.append({
            'target_coverage': target,
            'initial_coverage': initial_coverage,
            'final_coverage': final_coverage,
            'additional_sensors': additional_sensors,
            'total_sensors': len(optimized_stations),
            'achieved': achieved,
            'cost_per_improvement': additional_sensors / max(final_coverage - initial_coverage, 0.001)
        })
        
        print(f"初始覆盖率: {initial_coverage*100:.2f}%")
        print(f"最终覆盖率: {final_coverage*100:.2f}%")
        print(f"需要新增: {additional_sensors} 个传感器")
        print(f"达到目标: {'是' if achieved else '否'}")
    
    # 绘制成本效益分析图
    plot_cost_effectiveness(cost_analysis)
    
    return cost_analysis

def visualize_additional_stations_comparison(solver, original_stations, final_stations, 
                                           new_stations, initial_coverage, final_coverage):
    """可视化新增传感器前后的对比"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # 绘制原始方案
    plot_station_layout(ax1, solver, original_stations, 
                       f"原始方案 (覆盖率: {initial_coverage*100:.1f}%)")
    
    # 绘制优化方案（突出新增传感器）
    plot_station_layout_with_new(ax2, solver, original_stations, new_stations, 
                                f"优化方案 (覆盖率: {final_coverage*100:.1f}%)")
    
    plt.tight_layout()
    plt.show()

def plot_station_layout_with_new(ax, solver, original_stations, new_stations, title):
    """绘制包含新增传感器的布局"""
    # 绘制目标区域
    x_coords, y_coords = zip(*solver.target_area_coords)
    ax.plot(list(x_coords) + [x_coords[0]], 
            list(y_coords) + [y_coords[0]], 
            'b-', linewidth=2, label='目标区域')
    ax.fill(x_coords, y_coords, alpha=0.2, color='lightblue')
    
    # 绘制所有传感器的覆盖范围
    all_stations = original_stations + new_stations
    for i, station in enumerate(all_stations):
        color = 'red' if station in original_stations else 'green'
        alpha = 0.6 if station in original_stations else 0.8
        
        circle = plt.Circle(station, solver.sensor_radius, 
                          fill=False, color=color, alpha=alpha, linewidth=1.5)
        ax.add_patch(circle)
        
        # 填充覆盖区域
        circle_fill = plt.Circle(station, solver.sensor_radius, 
                               fill=True, color=color, alpha=0.1)
        ax.add_patch(circle_fill)
    
    # 绘制原有传感器
    if original_stations:
        orig_x, orig_y = zip(*original_stations)
        ax.scatter(orig_x, orig_y, c='red', s=100, 
                  marker='s', label=f'原有传感器 ({len(original_stations)}个)', 
                  edgecolors='black', linewidth=1, zorder=5)
    
    # 绘制新增传感器
    if new_stations:
        new_x, new_y = zip(*new_stations)
        ax.scatter(new_x, new_y, c='green', s=120, 
                  marker='^', label=f'新增传感器 ({len(new_stations)}个)', 
                  edgecolors='black', linewidth=1, zorder=5)
    
    # 标注传感器编号
    for i, (x, y) in enumerate(original_stations):
        ax.annotate(f'O{i+1}', (x, y), xytext=(5, 5), 
                   textcoords='offset points', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7))
    
    for i, (x, y) in enumerate(new_stations):
        ax.annotate(f'N{i+1}', (x, y), xytext=(5, 5), 
                   textcoords='offset points', fontsize=9,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='green', alpha=0.7))
    
    ax.set_xlabel('X 坐标')
    ax.set_ylabel('Y 坐标')
    ax.set_title(title, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    # 设置坐标轴范围
    minx, miny, maxx, maxy = solver.target_area.bounds
    margin = solver.sensor_radius * 0.5
    ax.set_xlim(minx - margin, maxx + margin)
    ax.set_ylim(miny - margin, maxy + margin)

def plot_cost_effectiveness(cost_analysis):
    """绘制成本效益分析图"""
    targets = [c['target_coverage']*100 for c in cost_analysis]
    additional_sensors = [c['additional_sensors'] for c in cost_analysis]
    final_coverages = [c['final_coverage']*100 for c in cost_analysis]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 新增传感器数量 vs 目标覆盖率
    bars1 = ax1.bar(range(len(targets)), additional_sensors, 
                   color=['lightgreen' if c['achieved'] else 'lightcoral' for c in cost_analysis],
                   alpha=0.8)
    
    ax1.set_xlabel('目标覆盖率 (%)')
    ax1.set_ylabel('需要新增的传感器数量')
    ax1.set_title('新增传感器数量 vs 目标覆盖率', fontweight='bold')
    ax1.set_xticks(range(len(targets)))
    ax1.set_xticklabels([f'{t:.0f}%' for t in targets])
    ax1.grid(True, alpha=0.3)
    
    # 在柱子上添加数值标签
    for bar, count in zip(bars1, additional_sensors):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                f'{count}', ha='center', va='bottom', fontsize=10)
    
    # 实际达到的覆盖率
    line = ax2.plot(targets, final_coverages, 'bo-', linewidth=2, markersize=8, label='实际覆盖率')
    ax2.plot(targets, targets, 'r--', linewidth=2, label='目标覆盖率', alpha=0.7)
    
    ax2.set_xlabel('目标覆盖率 (%)')
    ax2.set_ylabel('实际达到的覆盖率 (%)')
    ax2.set_title('目标 vs 实际覆盖率', fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 标注未达标的点
    for i, c in enumerate(cost_analysis):
        if not c['achieved']:
            ax2.annotate('未达标', (targets[i], final_coverages[i]), 
                        xytext=(10, 10), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='red', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', color='red'))
    
    plt.tight_layout()
    plt.show()

def main():
    """运行所有演示"""
    print("传感器布设优化功能完整演示")
    print("="*60)
    
    # 1. 基本优化演示（仅位置优化）
    demo_station_optimization()
    
    # 2. 不同目标覆盖率比较
    demo_different_target_coverage()
    
    # 3. 迭代过程演示
    demo_iterative_optimization()
    
    # 4. 新增传感器优化演示
    demo_additional_stations_optimization()
    
    # 5. 智能优化策略演示
    demo_smart_optimization()
    
    # 6. 成本效益分析
    demo_cost_effectiveness_analysis()
    
    print(f"\n" + "="*60)
    print("所有演示完成！")
    print("="*60)
    
    print(f"\n功能总结:")
    print(f"1. optimize_existing_stations() - 优化已有传感器位置（不增加数量）")
    print(f"2. optimize_with_additional_stations() - 新增传感器优化（可增加数量）")
    print(f"3. smart_station_optimization() - 智能优化策略选择")
    print(f"4. compare_station_layouts() - 比较优化前后效果")
    print(f"5. 支持设定目标覆盖率和最大新增数量")
    print(f"6. 提供详细的优化统计和成本效益分析")
    print(f"7. 可视化优化结果对比（含新增传感器标识）")

if __name__ == "__main__":
    main()