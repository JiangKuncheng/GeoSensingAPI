"""
GeoJSON格式六个算法演示运行器

提供GeoJSON格式的六个核心算法演示入口，展示标准化的输入输出格式
"""

import json
import sys

def main():
    print("="*70)
    print("GeoSensingAPI 传感器网络优化演示 (GeoJSON格式)")
    print("="*70)
    print()
    print("所有算法现已支持标准GeoJSON格式输入输出：")
    print()
    print("🏠 地面传感器优化系列 (GeoJSON):")
    print("  1. 地面传感器从零布设 (GeoJSON)")
    print("  2. 地面传感器位置优化 (GeoJSON)")
    print("  3. 地面传感器增补优化 (GeoJSON)")
    print()
    print("🛰️ 混合传感器优化系列 (GeoJSON):")
    print("  4. 混合传感器从零布设 (GeoJSON)")
    print("  5. 混合传感器位置优化 (GeoJSON)")
    print("  6. 混合传感器增补优化 (GeoJSON)")
    print()
    print("🧪 测试和验证:")
    print("  7. 运行所有算法GeoJSON功能测试")
    print("  8. 查看GeoJSON输出示例")
    print()
    print("  0. 退出")
    print()
    
    try:
        choice = input("请输入选择 (0-8): ").strip()
        
        if choice == '0':
            print("再见！")
            return
        elif choice == '1':
            print("\n启动地面传感器从零布设演示 (GeoJSON)...")
            from geojson_ground_sensor_from_scratch import demo_geojson_ground_sensor_from_scratch
            demo_geojson_ground_sensor_from_scratch()
        elif choice == '2':
            print("\n启动地面传感器位置优化演示 (GeoJSON)...")
            from geojson_ground_sensor_position_optimize import demo_geojson_ground_sensor_position_optimize
            demo_geojson_ground_sensor_position_optimize()
        elif choice == '3':
            print("\n启动地面传感器增补优化演示 (GeoJSON)...")
            print("该算法已集成在测试脚本中，使用GeoJSON格式输入输出")
            show_algorithm_3_example()
        elif choice == '4':
            print("\n启动混合传感器从零布设演示 (GeoJSON)...")
            print("该算法已集成在测试脚本中，使用GeoJSON格式输入输出")
            show_algorithm_4_example()
        elif choice == '5':
            print("\n启动混合传感器位置优化演示 (GeoJSON)...")
            print("该算法已集成在测试脚本中，使用GeoJSON格式输入输出")
            show_algorithm_5_example()
        elif choice == '6':
            print("\n启动混合传感器增补优化演示 (GeoJSON)...")
            print("该算法已集成在测试脚本中，使用GeoJSON格式输入输出")
            show_algorithm_6_example()
        elif choice == '7':
            print("\n运行所有算法GeoJSON功能测试...")
            from geojson_algorithms_test import main as test_main
            test_main()
        elif choice == '8':
            print("\n查看GeoJSON输出示例...")
            show_geojson_examples()
        else:
            print("无效选择，请重新运行程序")
            
    except KeyboardInterrupt:
        print("\n\n用户中断演示")
    except ImportError as e:
        print(f"\n导入错误: {e}")
        print("请确保所有依赖包已安装: pip install numpy matplotlib shapely")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")

def show_algorithm_3_example():
    """显示算法3的GeoJSON示例"""
    print("\n算法3 - 地面传感器增补优化 GeoJSON示例:")
    print("="*50)
    
    example_input = {
        "target_area_geojson": {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0], [10,0], [10,8], [0,8], [0,0]]]},
            "properties": {"name": "测试区域"}
        },
        "existing_sensors_geojson": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [2,2]}, "properties": {"id": 0}},
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [6,2]}, "properties": {"id": 1}}
            ]
        },
        "target_coverage": 0.9,
        "max_additional_stations": 3
    }
    
    example_output = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [2,2]}, "properties": {"id": 0, "status": "existing"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [6,2]}, "properties": {"id": 1, "status": "existing"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [8,6]}, "properties": {"id": 2, "status": "added"}}
        ],
        "properties": {
            "algorithm": "ground_sensor_addition_optimize",
            "original_coverage": 0.65,
            "final_coverage": 0.91,
            "added_sensors": 1
        }
    }
    
    print("输入格式示例:")
    print(json.dumps(example_input, indent=2, ensure_ascii=False))
    print("\n输出格式示例:")
    print(json.dumps(example_output, indent=2, ensure_ascii=False))

def show_algorithm_4_example():
    """显示算法4的GeoJSON示例"""
    print("\n算法4 - 混合传感器从零布设 GeoJSON示例:")
    print("="*50)
    
    example_input = {
        "target_area_geojson": {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0], [20,0], [20,15], [0,15], [0,0]]]},
            "properties": {"name": "大型监测区域"}
        },
        "satellites_geojson": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[1,0], [3,15]]}, 
                 "properties": {"id": 0, "swath_width": 3.0, "cost": 100}},
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[7,0], [9,15]]}, 
                 "properties": {"id": 1, "swath_width": 2.5, "cost": 90}}
            ]
        },
        "ground_sensors_geojson": {
            "type": "FeatureCollection", 
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [5,5]}, 
                 "properties": {"id": 0, "radius": 2.0, "cost": 10}},
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [15,10]}, 
                 "properties": {"id": 1, "radius": 2.5, "cost": 12}}
            ]
        },
        "constraints": {"max_satellites": 2, "max_ground_sensors": 3, "max_cost": 200}
    }
    
    example_output = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[1,0], [3,15]]}, 
             "properties": {"id": 0, "sensor_type": "selected_satellite", "cost": 100}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [5,5]}, 
             "properties": {"id": 0, "sensor_type": "selected_ground_sensor", "cost": 10}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [15,10]}, 
             "properties": {"id": 1, "sensor_type": "selected_ground_sensor", "cost": 12}}
        ],
        "properties": {
            "algorithm": "hybrid_sensor_from_scratch",
            "selected_satellites": 1,
            "selected_ground_sensors": 2,
            "total_cost": 122,
            "coverage_ratio": 0.92
        }
    }
    
    print("输入格式示例:")
    print(json.dumps(example_input, indent=2, ensure_ascii=False))
    print("\n输出格式示例:")
    print(json.dumps(example_output, indent=2, ensure_ascii=False))

def show_algorithm_5_example():
    """显示算法5的GeoJSON示例"""
    print("\n算法5 - 混合传感器位置优化 GeoJSON示例:")
    print("="*50)
    
    example_input = {
        "target_area_geojson": {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0], [20,0], [20,15], [0,15], [0,0]]]},
            "properties": {"name": "监测区域"}
        },
        "existing_satellites_geojson": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[2,0], [4,15]]}, 
                 "properties": {"id": 0, "swath_width": 3.0}}
            ]
        },
        "existing_ground_sensors_geojson": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10,8]}, 
                 "properties": {"id": 0, "radius": 2.0}},
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [15,5]}, 
                 "properties": {"id": 1, "radius": 2.0}}
            ]
        }
    }
    
    example_output = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[2,0], [4,15]]}, 
             "properties": {"id": 0, "status": "original", "sensor_type": "satellite"}},
            {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[2.2,0], [4.2,15]]}, 
             "properties": {"id": 0, "status": "optimized", "sensor_type": "satellite"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10.5,8.2]}, 
             "properties": {"id": 0, "status": "optimized", "sensor_type": "ground_sensor"}}
        ],
        "properties": {
            "algorithm": "hybrid_sensor_position_optimize",
            "original_coverage": 0.78,
            "optimized_coverage": 0.89,
            "improvement": 0.11
        }
    }
    
    print("输入格式示例:")
    print(json.dumps(example_input, indent=2, ensure_ascii=False))
    print("\n输出格式示例:")
    print(json.dumps(example_output, indent=2, ensure_ascii=False))

def show_algorithm_6_example():
    """显示算法6的GeoJSON示例"""
    print("\n算法6 - 混合传感器增补优化 GeoJSON示例:")
    print("="*50)
    
    example_input = {
        "target_area_geojson": {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [[[0,0], [25,0], [25,20], [0,20], [0,0]]]},
            "properties": {"name": "大型监测区域"}
        },
        "existing_satellites_geojson": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[3,0], [5,20]]}, 
                 "properties": {"id": 0, "swath_width": 3.0, "cost": 100}}
            ]
        },
        "existing_ground_sensors_geojson": {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10,10]}, 
                 "properties": {"id": 0, "radius": 2.5, "cost": 15}},
                {"type": "Feature", "geometry": {"type": "Point", "coordinates": [20,8]}, 
                 "properties": {"id": 1, "radius": 2.0, "cost": 12}}
            ]
        },
        "target_coverage": 0.95,
        "max_budget": 200
    }
    
    example_output = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[3,0], [5,20]]}, 
             "properties": {"id": 0, "status": "existing", "sensor_type": "satellite"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [10,10]}, 
             "properties": {"id": 0, "status": "existing", "sensor_type": "ground_sensor"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [20,8]}, 
             "properties": {"id": 1, "status": "existing", "sensor_type": "ground_sensor"}},
            {"type": "Feature", "geometry": {"type": "LineString", "coordinates": [[15,0], [17,20]]}, 
             "properties": {"id": 2, "status": "added", "sensor_type": "satellite", "cost": 95}}
        ],
        "properties": {
            "algorithm": "hybrid_sensor_addition_optimize",
            "original_coverage": 0.82,
            "final_coverage": 0.96,
            "added_satellites": 1,
            "added_ground_sensors": 0,
            "total_added_cost": 95
        }
    }
    
    print("输入格式示例:")
    print(json.dumps(example_input, indent=2, ensure_ascii=False))
    print("\n输出格式示例:")
    print(json.dumps(example_output, indent=2, ensure_ascii=False))

def show_geojson_examples():
    """显示GeoJSON输出示例"""
    print("\n查看已生成的GeoJSON文件:")
    print("="*50)
    
    try:
        with open('all_algorithms_test_result.geojson', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 找到测试结果文件: all_algorithms_test_result.geojson")
        print(f"   - 要素数量: {len(data['features'])}")
        print(f"   - 算法数量: {data['properties']['algorithms_tested']}")
        print(f"   - 描述: {data['properties']['description']}")
        
        print(f"\n前3个要素示例:")
        for i, feature in enumerate(data['features'][:3]):
            print(f"\n要素 {i+1}:")
            print(f"  - 类型: {feature['geometry']['type']}")
            print(f"  - 属性: {feature['properties']}")
            
    except FileNotFoundError:
        print("❌ 未找到测试结果文件，请先运行测试 (选项7)")
    except Exception as e:
        print(f"❌ 读取文件出错: {e}")
    
    print(f"\n所有算法均支持以下GeoJSON格式:")
    print(f"📥 输入: target_area_geojson (Polygon), sensors_geojson (FeatureCollection)")  
    print(f"📤 输出: result_geojson (FeatureCollection) 包含传感器位置和覆盖区域")
    print(f"🏷️ 属性: 算法参数、性能指标、优化结果等元数据")

if __name__ == "__main__":
    main()
