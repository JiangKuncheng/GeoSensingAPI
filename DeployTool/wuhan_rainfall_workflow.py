"""
武汉降雨观测任务完整工作流程
包含任务分析、发现阶段和数据处理
"""

import json
import os
import sys
from datetime import datetime, timedelta

# 添加工具路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'satelliteTool'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'GeoPandasTool'))

from get_TLE_data import get_tle
from getPlaceBoundary import get_boundary
from get_observation_lace import get_coverage_lace
from has_intersection import has_intersection

def stage1_task_analysis():
    """第1阶段：任务需求分析"""
    print("=" * 60)
    print("📋 第1阶段：任务需求分析")
    print("=" * 60)
    
    # 用户原始需求
    user_requirement = "观测武汉最近七天降雨"
    print(f"用户原始需求: {user_requirement}")
    
    # 结构化需求
    structured_requirement = {
        "监测目标": "降雨",
        "监测区域": "武汉市",
        "时间范围": "最近七天",
        "监测参数": ["降雨量", "降雨分布"]
    }
    
    print(f"\n结构化需求:")
    print(json.dumps(structured_requirement, ensure_ascii=False, indent=2))
    
    print(f"\n需求分析结果:")
    print(f"- 任务类型: 气象观测")
    print(f"- 空间范围: 城市级别")
    print(f"- 时间要求: 历史数据回溯")
    print(f"- 数据需求: 降雨监测数据")
    
    return structured_requirement

def stage2_discovery():
    """第2阶段：发现阶段"""
    print("\n" + "=" * 60)
    print("🔍 第2阶段：发现阶段")
    print("=" * 60)
    
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    # 2.1 获取武汉市边界
    print("\n2.1 获取武汉市边界...")
    try:
        wuhan_boundary_result = get_boundary("Wuhan")
        if isinstance(wuhan_boundary_result, dict) and "Wuhan" in wuhan_boundary_result:
            boundary_path = wuhan_boundary_result["Wuhan"]
            if boundary_path.endswith('.geojson') and os.path.exists(boundary_path):
                # 如果返回的是文件路径，读取文件内容
                with open(boundary_path, "r", encoding="utf-8") as f:
                    wuhan_boundary = json.load(f)
                # 复制到data目录
                with open("data/wuhan_boundary.geojson", "w", encoding="utf-8") as f:
                    json.dump(wuhan_boundary, f, ensure_ascii=False, indent=2)
            else:
                raise Exception(f"边界获取失败: {boundary_path}")
        else:
            raise Exception(f"边界获取失败: {wuhan_boundary_result}")
        print(f"✅ 成功获取武汉市边界数据")
        print(f"✅ 边界数据已保存到: data/wuhan_boundary.geojson")
        
    except Exception as e:
        print(f"❌ 获取武汉边界失败: {e}")
        # 创建模拟的武汉边界数据
        wuhan_boundary = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon", 
                    "coordinates": [[[114.0, 30.3], [114.8, 30.3], [114.8, 30.9], [114.0, 30.9], [114.0, 30.3]]]
                },
                "properties": {"name": "武汉市"}
            }]
        }
        with open("data/wuhan_boundary.geojson", "w", encoding="utf-8") as f:
            json.dump(wuhan_boundary, f, ensure_ascii=False, indent=2)
        print(f"⚠️  使用模拟边界数据: data/wuhan_boundary.geojson")
    
    # 2.2 批量获取卫星TLE数据
    print("\n2.2 批量获取卫星TLE数据...")
    
    # 指定的卫星列表
    target_satellites = [
        # 资源系列
        "ZIYUAN 1-02C",
        "ZIYUAN 3",
        # 高分系列
        "GAOFEN-1",
        "GAOFEN-2", 
        "GAOFEN-3",
        "GAOFEN-4",
        "GAOFEN-5",
        "GAOFEN-6",
        "GAOFEN-7",
        # 气象卫星
        "NOAA 19",
        "TERRA",
        "AQUA"
    ]
    
    try:
        satellite_tle_data = get_tle(target_satellites)
        available_satellites = {}
        
        for sat_name, tle in satellite_tle_data.items():
            if isinstance(tle, str) and "Error" not in tle and "No GP data found" not in tle:
                available_satellites[sat_name] = tle
                print(f"✅ {sat_name}: TLE数据获取成功")
            else:
                print(f"❌ {sat_name}: {tle}")
        
        print(f"\n📊 可用卫星统计: {len(available_satellites)}/{len(target_satellites)}")
        
    except Exception as e:
        print(f"❌ TLE数据获取失败: {e}")
        return False
    
    # 2.3 计算卫星覆盖轨迹并判断与武汉的交集
    print("\n2.3 计算卫星覆盖轨迹并判断与武汉的交集...")
    
    # 计算时间范围（最近7天）
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S.%f")
    
    # 准备卫星配置
    satellite_names = list(available_satellites.keys())  # 计算所有可用卫星
    
    satellite_configs = []
    for i, sat_name in enumerate(satellite_names):
        tle_data = available_satellites[sat_name]
        output_path = f"data/satellite_coverage_{i+1}.geojson"
        
        satellite_configs.append({
            "tle_str": tle_data,
            "start_time_str": start_time_str,
            "end_time_str": end_time_str,
            "interval": 7200,  # 2小时间隔
            "fov": 60,    # 视场角60度
            "output_path": output_path
        })
    
    try:
        if satellite_names:
            # 计算所有卫星覆盖轨迹
            coverage_results = get_coverage_lace(satellite_configs)
            
            print(f"卫星覆盖轨迹计算结果:")
            for i, sat_name in enumerate(satellite_names):
                output_path = f"data/satellite_coverage_{i+1}.geojson"
                print(f"  {sat_name}: {coverage_results.get(output_path, '未知错误')}")
            
            # 读取武汉区域数据
            with open("data/wuhan_boundary.geojson", "r", encoding="utf-8") as f:
                wuhan_data = json.load(f)
            
            # 判断哪些卫星与武汉有交集
            print(f"\n判断卫星轨迹与武汉区域的交集:")
            valid_satellites = []
            
            for i, sat_name in enumerate(satellite_names):
                coverage_file = f"data/satellite_coverage_{i+1}.geojson"
                
                if os.path.exists(coverage_file):
                    with open(coverage_file, "r", encoding="utf-8") as f:
                        coverage_data = json.load(f)
                    
                    intersection_result = has_intersection(
                        json.dumps(coverage_data),
                        json.dumps(wuhan_data)
                    )
                    
                    print(f"  {sat_name}: {intersection_result}")
                    if intersection_result == "True":
                        valid_satellites.append(sat_name)
            
            # 输出结果
            print(f"\n📊 有效观测卫星: {len(valid_satellites)}/{len(satellite_names)}")
            
            if valid_satellites:
                print("✅ 发现阶段完成：找到可用于武汉降雨观测的卫星数据")
                for sat in valid_satellites:
                    print(f"  - {sat}")
            else:
                print("❌ 未找到与武汉区域有交集的卫星观测数据")
                
        else:
            print("❌ 没有可用卫星进行覆盖计算")
            return False
            
    except Exception as e:
        print(f"❌ 卫星覆盖计算失败: {e}")
        return False
    
    return True

def stage3_configuration():
    """第3阶段：配置阶段"""
    print("\n" + "=" * 60)
    print("⚙️ 第3阶段：配置阶段")
    print("=" * 60)
    print("说明: 配置阶段代码在同门那里，暂时不实现")
    print("当前任务为历史数据回溯分析，不需要新建观测网络配置")

def main():
    """主函数"""
    print("🛰️ 武汉降雨观测任务工作流程")
    print("包含: 任务分析 + 发现阶段 + 配置阶段")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # 第1阶段：任务需求分析
        structured_req = stage1_task_analysis()
        
        # 第2阶段：发现阶段
        discovery_success = stage2_discovery()
        
        # 第3阶段：配置阶段
        stage3_configuration()
        
        # 总结
        print("\n" + "=" * 60)
        print("🎯 工作流程完成总结")
        print("=" * 60)
        print("✅ 第1阶段: 任务需求分析 - 完成")
        print(f"{'✅' if discovery_success else '❌'} 第2阶段: 发现阶段 - {'完成' if discovery_success else '部分失败'}")
        print("⏸️  第3阶段: 配置阶段 - 跳过")
        
        # 列出生成的文件
        print(f"\n📁 生成的数据文件:")
        data_files = [f for f in os.listdir("data") if f.endswith('.geojson')]
        for i, file in enumerate(data_files, 1):
            file_path = os.path.join("data", file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            print(f"  {i}. {file} ({file_size:.1f} KB)")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断程序执行")
    except Exception as e:
        print(f"\n❌ 程序执行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
