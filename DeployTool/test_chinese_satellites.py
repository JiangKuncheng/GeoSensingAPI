"""
测试中国资源和高分系列卫星TLE数据
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'satelliteTool'))

from get_TLE_data import get_tle
import time

def test_satellites():
    """测试资源和高分系列卫星"""
    
    # 资源系列 - 使用统一命名
    ziyuan_satellites = [
        "ZIYUAN 1-02C",
        "ZIYUAN 1-02D", 
        "ZIYUAN 1-02E",
        "ZIYUAN 3",
        "ZIYUAN 3-01",
        "ZIYUAN 3-02",
        "ZIYUAN 3-03",
        "ZIYUAN-1",
        "ZIYUAN-3"
    ]
    
    # 高分系列
    gaofen_satellites = [
        "GAOFEN-1",
        "GAOFEN-2", 
        "GAOFEN-3",
        "GAOFEN-4",
        "GAOFEN-5",
        "GAOFEN-6",
        "GAOFEN-7"
    ]
    
    print("🛰️ 中国卫星TLE数据测试")
    print("="*40)
    
    all_success = {}
    
    # 测试资源系列
    print("\n📡 资源系列:")
    for sat in ziyuan_satellites:
        try:
            tle = get_tle(sat)
            if isinstance(tle, str) and "No GP data found" not in tle and "Error" not in tle:
                lines = tle.split('\n')
                if len(lines) >= 3:
                    print(f"✅ {sat} -> {lines[0].strip()}")
                    all_success[sat] = lines[0].strip()
                else:
                    print(f"❌ {sat} 数据不完整")
            else:
                print(f"❌ {sat} 未找到")
        except:
            print(f"❌ {sat} 错误")
        time.sleep(0.1)
    
    # 测试高分系列
    print("\n📡 高分系列:")
    for sat in gaofen_satellites:
        try:
            tle = get_tle(sat)
            if isinstance(tle, str) and "No GP data found" not in tle and "Error" not in tle:
                lines = tle.split('\n')
                if len(lines) >= 3:
                    print(f"✅ {sat} -> {lines[0].strip()}")
                    all_success[sat] = lines[0].strip()
                else:
                    print(f"❌ {sat} 数据不完整")
            else:
                print(f"❌ {sat} 未找到")
        except:
            print(f"❌ {sat} 错误")
        time.sleep(0.1)
    
    # 总结
    print(f"\n📊 结果汇总:")
    print(f"总测试: {len(ziyuan_satellites + gaofen_satellites)}个")
    print(f"成功: {len(all_success)}个")
    
    if all_success:
        print(f"\n✅ 可用卫星列表:")
        for i, (query, actual) in enumerate(all_success.items(), 1):
            print(f"{i:2d}. {query} -> {actual}")

if __name__ == "__main__":
    test_satellites()
