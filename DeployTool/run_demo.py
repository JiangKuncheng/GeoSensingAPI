"""
传感器网络优化演示启动器

提供所有六个核心功能的快速演示入口
"""

import sys

def main():
    print("="*70)
    print("GeoSensingAPI 传感器网络优化演示")
    print("="*70)
    print()
    print("请选择要演示的功能：")
    print()
    print("🏠 地面传感器优化系列:")
    print("  1. 地面传感器从零布设")
    print("  2. 地面传感器位置优化")
    print("  3. 地面传感器增补优化")
    print()
    print("🛰️ 混合传感器优化系列:")
    print("  4. 混合传感器从零布设")
    print("  5. 混合传感器位置优化")
    print("  6. 混合传感器增补优化")
    print()
    print("📁 演示集合:")
    print("  7. 地面传感器示例演示")
    print("  8. 优化策略对比演示")
    print("  9. 高级算法演示")
    print()
    print("  0. 退出")
    print()
    
    try:
        choice = input("请输入选择 (0-9): ").strip()
        
        if choice == '0':
            print("再见！")
            return
        elif choice == '1':
            print("\n启动地面传感器从零布设演示...")
            from ground_sensor_from_scratch import demo_ground_sensor_from_scratch
            demo_ground_sensor_from_scratch()
        elif choice == '2':
            print("\n启动地面传感器位置优化演示...")
            from ground_sensor_position_optimize import demo_ground_sensor_position_optimize
            demo_ground_sensor_position_optimize()
        elif choice == '3':
            print("\n启动地面传感器增补优化演示...")
            from ground_sensor_addition_optimize import demo_ground_sensor_addition_optimize
            demo_ground_sensor_addition_optimize()
        elif choice == '4':
            print("\n启动混合传感器从零布设演示...")
            from hybrid_sensor_from_scratch import demo_hybrid_sensor_from_scratch
            demo_hybrid_sensor_from_scratch()
        elif choice == '5':
            print("\n启动混合传感器位置优化演示...")
            from hybrid_sensor_position_optimize import demo_hybrid_sensor_position_optimize
            demo_hybrid_sensor_position_optimize()
        elif choice == '6':
            print("\n启动混合传感器增补优化演示...")
            from hybrid_sensor_addition_optimize import demo_hybrid_sensor_addition_optimize
            demo_hybrid_sensor_addition_optimize()
        elif choice == '7':
            print("\n启动地面传感器示例演示...")
            from demos.mclp_examples import main as demo_mclp
            demo_mclp()
        elif choice == '8':
            print("\n启动优化策略对比演示...")
            from demos.optimization_demo import main as demo_opt
            demo_opt()
        elif choice == '9':
            print("\n启动高级算法演示...")
            from demos.advanced_optimization_demo import main as demo_advanced
            demo_advanced()
        else:
            print("无效选择，请重新运行程序")
            
    except KeyboardInterrupt:
        print("\n\n用户中断演示")
    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("请确保所有依赖包已安装: pip install numpy matplotlib shapely geopandas")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")

if __name__ == "__main__":
    main()