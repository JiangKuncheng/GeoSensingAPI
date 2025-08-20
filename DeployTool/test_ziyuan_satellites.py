"""
测试资源系列卫星TLE数据获取
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'satelliteTool'))

from get_TLE_data import get_tle
import time

def test_ziyuan_satellites():
    """测试资源系列卫星TLE获取"""
    
    # 资源系列卫星名称变体
    ziyuan_satellites = [
        # 资源一号02E星(ZY1F)
        "ZY1F",
        "ZY-1F", 
        "ZIYUAN 1F",
        "ZIYUAN-1F",
        "ZIYUAN 1 02E",
        "资源一号02E",
        
        # 资源三号03星(ZY303)
        "ZY303",
        "ZY-303",
        "ZY3-03",
        "ZIYUAN 3-03",
        "ZIYUAN-3-03",
        "ZIYUAN 303",
        
        # 资源一号02D星(ZY1E)
        "ZY1E",
        "ZY-1E",
        "ZIYUAN 1E",
        "ZIYUAN-1E", 
        "ZIYUAN 1 02D",
        
        # 资源三号2号卫星(ZY302)
        "ZY302",
        "ZY-302",
        "ZY3-02",
        "ZIYUAN 3-02",
        "ZIYUAN-3-02",
        "ZIYUAN 302",
        
        # 资源三号卫星(ZY3)
        "ZY3",
        "ZY-3",
        "ZIYUAN 3",
        "ZIYUAN-3",
        
        # 资源一号02C卫星(ZY02C)
        "ZY02C",
        "ZY-02C",
        "ZY1C",
        "ZY-1C",
        "ZIYUAN 1C",
        "ZIYUAN-1C",
        "ZIYUAN 02C"
    ]
    
    print("🛰️ 测试资源系列卫星TLE数据获取")
    print("="*50)
    
    successful_satellites = {}
    failed_satellites = []
    
    for satellite_name in ziyuan_satellites:
        print(f"测试: {satellite_name}")
        
        try:
            tle_data = get_tle(satellite_name)
            
            if isinstance(tle_data, str) and "No GP data found" not in tle_data and not tle_data.startswith("Error"):
                lines = tle_data.strip().split('\n')
                if len(lines) >= 3:
                    print(f"  ✅ 成功! 卫星名: {lines[0]}")
                    successful_satellites[satellite_name] = lines[0]
                else:
                    print(f"  ❌ 数据不完整")
                    failed_satellites.append(satellite_name)
            else:
                print(f"  ❌ 未找到")
                failed_satellites.append(satellite_name)
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            failed_satellites.append(satellite_name)
        
        time.sleep(0.2)  # 避免请求过快
    
    # 统计结果
    print("\n" + "="*50)
    print("📊 资源系列卫星TLE获取结果")
    print("="*50)
    
    if successful_satellites:
        print(f"✅ 成功获取TLE数据的卫星 ({len(successful_satellites)}个):")
        for query_name, actual_name in successful_satellites.items():
            print(f"  查询名称: {query_name}")
            print(f"  实际名称: {actual_name}")
            print()
    else:
        print("❌ 未能成功获取任何资源系列卫星的TLE数据")
    
    if failed_satellites:
        print(f"❌ 未找到TLE数据的查询名称 ({len(failed_satellites)}个):")
        for name in failed_satellites[:10]:  # 只显示前10个
            print(f"  {name}")
        if len(failed_satellites) > 10:
            print(f"  ... 还有 {len(failed_satellites) - 10} 个")
    
    return successful_satellites

def test_other_chinese_earth_observation():
    """测试其他中国对地观测卫星"""
    
    other_satellites = [
        # 环境减灾
        "HJ-1A",
        "HJ-1B", 
        "HJ1A",
        "HJ1B",
        "HUANJING",
        
        # 海洋系列
        "HY-1",
        "HY-2",
        "HY1",
        "HY2",
        "HAIYANG",
        
        # 天绘系列
        "TH-1",
        "TH1",
        "TIANHUI",
        
        # 遥感系列
        "YG-1",
        "YG1",
        "YAOGAN"
    ]
    
    print("\n🛰️ 测试其他中国对地观测卫星")
    print("="*50)
    
    successful = {}
    
    for satellite_name in other_satellites:
        print(f"测试: {satellite_name}")
        
        try:
            tle_data = get_tle(satellite_name)
            
            if isinstance(tle_data, str) and "No GP data found" not in tle_data and not tle_data.startswith("Error"):
                lines = tle_data.strip().split('\n')
                if len(lines) >= 3:
                    print(f"  ✅ 成功! 卫星名: {lines[0]}")
                    successful[satellite_name] = lines[0]
                else:
                    print(f"  ❌ 数据不完整")
            else:
                print(f"  ❌ 未找到")
                
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        time.sleep(0.2)
    
    if successful:
        print(f"\n✅ 其他中国对地观测卫星成功 ({len(successful)}个):")
        for query_name, actual_name in successful.items():
            print(f"  {query_name} -> {actual_name}")
    
    return successful

def main():
    print("🇨🇳 中国对地观测卫星TLE数据测试")
    print("包括: 资源系列 + 高分系列 + 其他系列")
    print()
    
    # 测试资源系列
    ziyuan_success = test_ziyuan_satellites()
    
    # 测试其他系列
    other_success = test_other_chinese_earth_observation()
    
    # 总结
    print("\n" + "="*50)
    print("🎯 总体测试结果")
    print("="*50)
    print(f"资源系列成功: {len(ziyuan_success)}个")
    print(f"其他系列成功: {len(other_success)}个")
    print(f"总计可用卫星: {len(ziyuan_success) + len(other_success)}个")
    
    all_successful = {**ziyuan_success, **other_success}
    
    if all_successful:
        print(f"\n📋 所有可用的中国对地观测卫星:")
        for i, (query_name, actual_name) in enumerate(all_successful.items(), 1):
            print(f"  {i}. {actual_name} (查询: {query_name})")

if __name__ == "__main__":
    main()
