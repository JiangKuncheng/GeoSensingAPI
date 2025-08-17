"""
空间-地面传感器网络启发式优化演示脚本

该脚本演示如何使用遗传算法和模拟退火算法来解决
大规模传感器选址问题，包括：

1. 基本的传感器选择优化
2. 资源约束下的帕累托前沿分析
3. 动态环境下的传感器重配置
4. 不同算法的性能比较

运行示例：
python advanced_optimization_demo.py
"""

from advanced_sensor_optimization import *
import sys

def simple_optimization_example():
    """简单优化示例 - 适合快速测试"""
    print("="*60)
    print("简单传感器网络优化示例")
    print("="*60)
    
    # 创建简单的测试场景
    target_area = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    
    # 创建几个卫星（条带状覆盖）
    satellites = [
        Satellite(0, start_x=1, start_y=0, end_x=9, end_y=10, swath_width=3, cost=80),  # 南北向轨道
        Satellite(1, start_x=0, start_y=3, end_x=10, end_y=7, swath_width=2.5, cost=90),  # 东西向轨道
        Satellite(2, start_x=2, start_y=0, end_x=8, end_y=10, swath_width=3.5, cost=85),  # 轻微倾斜轨道
        Satellite(3, start_x=0, start_y=1, end_x=10, end_y=9, swath_width=2.8, cost=95)   # 斜向轨道
    ]
    
    # 创建几个地面传感器
    ground_sensors = [
        GroundSensor(0, 2, 2, 2.0, cost=10),
        GroundSensor(1, 8, 2, 2.0, cost=12),
        GroundSensor(2, 2, 8, 2.0, cost=11),
        GroundSensor(3, 8, 8, 2.0, cost=13),
        GroundSensor(4, 5, 5, 2.5, cost=15)
    ]
    
    # 设置约束
    constraints = ResourceConstraints(
        max_satellites=2,
        max_ground_sensors=3,
        max_total_cost=200,
        target_coverage_ratio=0.8
    )
    
    print(f"场景信息:")
    print(f"- 目标区域: 10x10 矩形")
    print(f"- 候选卫星: {len(satellites)} 个")
    print(f"- 候选地面传感器: {len(ground_sensors)} 个")
    print(f"- 目标覆盖率: {constraints.target_coverage_ratio*100}%")
    print(f"- 成本预算: {constraints.max_total_cost}")
    
    # 使用遗传算法
    print(f"\n使用遗传算法优化...")
    ga_optimizer = GeneticAlgorithmOptimizer(
        target_area=target_area,
        satellites=satellites,
        ground_sensors=ground_sensors,
        constraints=constraints,
        population_size=20,
        generations=30,
        grid_resolution=0.5
    )
    
    ga_solution = ga_optimizer.optimize()
    
    print(f"\n遗传算法结果:")
    print(f"- 选择的卫星: {ga_solution.selected_satellites}")
    print(f"- 选择的地面传感器: {ga_solution.selected_ground_sensors}")
    print(f"- 覆盖率: {ga_solution.coverage_ratio*100:.1f}%")
    print(f"- 总成本: {ga_solution.total_cost:.1f}")
    print(f"- 达到目标: {'是' if ga_solution.coverage_ratio >= constraints.target_coverage_ratio else '否'}")
    
    # 可视化结果
    ga_optimizer.visualize_solution(ga_solution, "简单优化示例结果")
    
    return ga_optimizer, ga_solution

def comprehensive_comparison_example():
    """综合比较示例"""
    print("\n" + "="*60)
    print("综合算法比较示例")
    print("="*60)
    
    # 创建更复杂的场景
    target_area = Polygon([(0, 0), (15, 0), (15, 12), (0, 12)])
    
    # 随机生成传感器
    np.random.seed(42)
    random.seed(42)
    
    satellites = []
    for i in range(6):
        # 生成不同方向的轨道
        if i % 3 == 0:  # 南北向
            start_x = np.random.uniform(2, 13)
            start_y = 0
            end_x = start_x + np.random.uniform(-2, 2)
            end_y = 12
        elif i % 3 == 1:  # 东西向
            start_x = 0
            start_y = np.random.uniform(2, 10)
            end_x = 15
            end_y = start_y + np.random.uniform(-2, 2)
        else:  # 斜向
            start_x = np.random.uniform(0, 5)
            start_y = 0
            end_x = start_x + np.random.uniform(8, 12)
            end_y = 12
        
        swath_width = np.random.uniform(2, 4)
        cost = np.random.uniform(70, 120)
        satellites.append(Satellite(i, start_x, start_y, end_x, end_y, swath_width, cost))
    
    ground_sensors = []
    for i in range(10):
        x = np.random.uniform(1, 14)
        y = np.random.uniform(1, 11)
        radius = np.random.uniform(1.5, 3.0)
        cost = np.random.uniform(8, 15)
        ground_sensors.append(GroundSensor(i, x, y, radius, cost))
    
    constraints = ResourceConstraints(
        max_satellites=3,
        max_ground_sensors=5,
        max_total_cost=300,
        target_coverage_ratio=0.85
    )
    
    print(f"复杂场景信息:")
    print(f"- 目标区域: 15x12 矩形")
    print(f"- 候选卫星: {len(satellites)} 个")
    print(f"- 候选地面传感器: {len(ground_sensors)} 个")
    print(f"- 目标覆盖率: {constraints.target_coverage_ratio*100}%")
    
    results = {}
    
    # 遗传算法
    print(f"\n--- 遗传算法优化 ---")
    start_time = time.time()
    ga_optimizer = GeneticAlgorithmOptimizer(
        target_area, satellites, ground_sensors, constraints,
        population_size=30, generations=40, grid_resolution=0.6
    )
    ga_solution = ga_optimizer.optimize()
    ga_time = time.time() - start_time
    
    results['GA'] = {
        'solution': ga_solution,
        'time': ga_time,
        'optimizer': ga_optimizer
    }
    
    # 模拟退火
    print(f"\n--- 模拟退火优化 ---")
    start_time = time.time()
    sa_optimizer = SimulatedAnnealingOptimizer(
        target_area, satellites, ground_sensors, constraints,
        max_iterations=500, grid_resolution=0.6
    )
    sa_solution = sa_optimizer.optimize()
    sa_time = time.time() - start_time
    
    results['SA'] = {
        'solution': sa_solution,
        'time': sa_time,
        'optimizer': sa_optimizer
    }
    
    # 结果比较
    print(f"\n" + "="*50)
    print(f"算法性能比较")
    print(f"="*50)
    print(f"{'指标':<15} {'遗传算法':<12} {'模拟退火':<12}")
    print(f"-" * 45)
    print(f"{'覆盖率(%)':<15} {results['GA']['solution'].coverage_ratio*100:<12.1f} {results['SA']['solution'].coverage_ratio*100:<12.1f}")
    print(f"{'总成本':<15} {results['GA']['solution'].total_cost:<12.1f} {results['SA']['solution'].total_cost:<12.1f}")
    print(f"{'计算时间(s)':<15} {results['GA']['time']:<12.1f} {results['SA']['time']:<12.1f}")
    print(f"{'卫星数量':<15} {len(results['GA']['solution'].selected_satellites):<12} {len(results['SA']['solution'].selected_satellites):<12}")
    print(f"{'地面站数量':<15} {len(results['GA']['solution'].selected_ground_sensors):<12} {len(results['SA']['solution'].selected_ground_sensors):<12}")
    
    # 可视化最佳结果
    best_algorithm = 'GA' if results['GA']['solution'].coverage_ratio >= results['SA']['solution'].coverage_ratio else 'SA'
    best_result = results[best_algorithm]
    
    print(f"\n最佳算法: {best_algorithm}")
    best_result['optimizer'].visualize_solution(
        best_result['solution'], 
        f"最佳结果 - {best_algorithm}"
    )
    
    return results

def resource_optimization_example():
    """资源优化示例"""
    print("\n" + "="*60)
    print("资源平衡优化示例")
    print("="*60)
    
    # 使用前面的场景
    target_area = Polygon([(0, 0), (12, 0), (12, 10), (0, 10)])
    
    # 创建传感器（条带状卫星覆盖）
    satellites = [
        Satellite(0, start_x=2, start_y=0, end_x=4, end_y=10, swath_width=3, cost=80),    # 南北向
        Satellite(1, start_x=8, start_y=0, end_x=10, end_y=10, swath_width=3, cost=90),  # 南北向
        Satellite(2, start_x=0, start_y=3, end_x=12, end_y=5, swath_width=2.5, cost=85),  # 东西向
        Satellite(3, start_x=0, start_y=7, end_x=12, end_y=9, swath_width=2.5, cost=95),  # 东西向
    ]
    
    ground_sensors = [
        GroundSensor(0, 2, 2, 2.0, cost=10),
        GroundSensor(1, 6, 2, 2.0, cost=12),
        GroundSensor(2, 10, 2, 2.0, cost=11),
        GroundSensor(3, 2, 5, 2.0, cost=13),
        GroundSensor(4, 6, 5, 2.0, cost=15),
        GroundSensor(5, 10, 5, 2.0, cost=14),
        GroundSensor(6, 2, 8, 2.0, cost=12),
        GroundSensor(7, 6, 8, 2.0, cost=16),
        GroundSensor(8, 10, 8, 2.0, cost=13),
    ]
    
    constraints = ResourceConstraints(
        max_satellites=4,
        max_ground_sensors=6,
        max_total_cost=500,  # 会根据预算调整
        target_coverage_ratio=0.8
    )
    
    print(f"资源优化场景:")
    print(f"- 传感器总数: {len(satellites) + len(ground_sensors)}")
    print(f"- 测试不同预算水平的影响")
    
    # 创建基础优化器
    base_optimizer = GeneticAlgorithmOptimizer(
        target_area, satellites, ground_sensors, constraints,
        population_size=20, generations=25, grid_resolution=0.8
    )
    
    # 资源平衡优化
    resource_optimizer = ResourceBalanceOptimizer(base_optimizer)
    
    budget_levels = [150, 200, 250, 300, 350]
    print(f"\n测试预算水平: {budget_levels}")
    
    pareto_solutions = resource_optimizer.multi_objective_optimization(budget_levels)
    
    # 分析结果
    if pareto_solutions:
        print(f"\n帕累托前沿解:")
        for i, sol in enumerate(pareto_solutions):
            print(f"解 {i+1}: 覆盖率={sol.coverage_ratio*100:.1f}%, "
                  f"成本={sol.total_cost:.1f}, "
                  f"传感器={len(sol.selected_satellites) + len(sol.selected_ground_sensors)}个")
        
        # 边际效率分析
        marginal_analysis = resource_optimizer.analyze_marginal_efficiency()
        if 'marginal_analysis' in marginal_analysis:
            print(f"\n边际效率分析:")
            for analysis in marginal_analysis['marginal_analysis']:
                print(f"成本 {analysis['cost_range']}: "
                      f"覆盖率提升 {analysis['coverage_increase']:.1f}%, "
                      f"边际效率 {analysis['marginal_efficiency']:.4f}")
        
        # 可视化帕累托前沿
        resource_optimizer.visualize_pareto_front()
    
    return resource_optimizer, pareto_solutions

def interactive_demo():
    """交互式演示"""
    print("\n" + "="*60)
    print("交互式传感器网络优化演示")
    print("="*60)
    
    print("选择演示类型:")
    print("1. 简单优化示例 (快速)")
    print("2. 综合算法比较 (中等)")
    print("3. 资源平衡优化 (详细)")
    print("4. 运行所有演示")
    
    try:
        choice = input("\n请输入选择 (1-4): ").strip()
        
        if choice == '1':
            simple_optimization_example()
        elif choice == '2':
            comprehensive_comparison_example()
        elif choice == '3':
            resource_optimization_example()
        elif choice == '4':
            print("运行所有演示...")
            simple_optimization_example()
            comprehensive_comparison_example()
            resource_optimization_example()
        else:
            print("无效选择，运行默认演示...")
            simple_optimization_example()
            
    except KeyboardInterrupt:
        print("\n用户中断演示")
    except Exception as e:
        print(f"演示过程中出现错误: {e}")

def batch_performance_test():
    """批量性能测试"""
    print("\n" + "="*60)
    print("批量性能测试")
    print("="*60)
    
    # 测试不同规模的问题
    test_scenarios = [
        {"name": "小规模", "area_size": (8, 8), "satellites": 4, "sensors": 6},
        {"name": "中规模", "area_size": (12, 10), "satellites": 6, "sensors": 10},
        {"name": "大规模", "area_size": (16, 12), "satellites": 8, "sensors": 15}
    ]
    
    performance_results = []
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']}问题测试 ---")
        
        # 创建测试场景
        area_width, area_height = scenario['area_size']
        target_area = Polygon([(0, 0), (area_width, 0), (area_width, area_height), (0, area_height)])
        
        # 生成传感器
        satellites = []
        for i in range(scenario['satellites']):
            # 生成随机轨道方向
            if i % 3 == 0:  # 南北向
                start_x = np.random.uniform(1, area_width-1)
                start_y = 0
                end_x = start_x + np.random.uniform(-1, 1)
                end_y = area_height
            elif i % 3 == 1:  # 东西向
                start_x = 0
                start_y = np.random.uniform(1, area_height-1)
                end_x = area_width
                end_y = start_y + np.random.uniform(-1, 1)
            else:  # 斜向
                start_x = np.random.uniform(0, area_width/3)
                start_y = 0
                end_x = start_x + np.random.uniform(area_width/2, area_width)
                end_y = area_height
            
            swath_width = np.random.uniform(1.5, 3)
            satellites.append(Satellite(i, start_x, start_y, end_x, end_y, swath_width))
        
        ground_sensors = []
        for i in range(scenario['sensors']):
            x = np.random.uniform(1, area_width-1)
            y = np.random.uniform(1, area_height-1)
            radius = np.random.uniform(1.0, 2.5)
            ground_sensors.append(GroundSensor(i, x, y, radius))
        
        constraints = ResourceConstraints(
            max_satellites=scenario['satellites']//2,
            max_ground_sensors=scenario['sensors']//2,
            target_coverage_ratio=0.8
        )
        
        # 测试遗传算法
        start_time = time.time()
        ga_optimizer = GeneticAlgorithmOptimizer(
            target_area, satellites, ground_sensors, constraints,
            population_size=15, generations=20, grid_resolution=1.0
        )
        ga_solution = ga_optimizer.optimize()
        ga_time = time.time() - start_time
        
        performance_results.append({
            'scenario': scenario['name'],
            'algorithm': 'GA',
            'coverage': ga_solution.coverage_ratio * 100,
            'time': ga_time,
            'sensors_used': len(ga_solution.selected_satellites) + len(ga_solution.selected_ground_sensors)
        })
        
        print(f"遗传算法: 覆盖率={ga_solution.coverage_ratio*100:.1f}%, 时间={ga_time:.1f}s")
    
    # 显示性能总结
    print(f"\n" + "="*50)
    print(f"性能测试总结")
    print(f"="*50)
    print(f"{'场景':<10} {'算法':<5} {'覆盖率(%)':<10} {'时间(s)':<8} {'传感器数':<8}")
    print(f"-" * 50)
    
    for result in performance_results:
        print(f"{result['scenario']:<10} {result['algorithm']:<5} "
              f"{result['coverage']:<10.1f} {result['time']:<8.1f} {result['sensors_used']:<8}")

def main():
    """主函数"""
    print("空间-地面传感器网络启发式优化算法演示")
    print("="*80)
    
    # 设置随机种子
    np.random.seed(42)
    random.seed(42)
    
    if len(sys.argv) > 1:
        # 命令行参数模式
        mode = sys.argv[1].lower()
        
        if mode == 'simple':
            simple_optimization_example()
        elif mode == 'compare':
            comprehensive_comparison_example()
        elif mode == 'resource':
            resource_optimization_example()
        elif mode == 'test':
            batch_performance_test()
        elif mode == 'full':
            # 运行完整演示
            from advanced_sensor_optimization import main as full_demo
            full_demo()
        else:
            print(f"未知模式: {mode}")
            print("可用模式: simple, compare, resource, test, full")
    else:
        # 交互模式
        interactive_demo()
    
    print(f"\n演示完成！")

if __name__ == "__main__":
    main()