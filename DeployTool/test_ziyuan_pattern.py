"""
基于成功命名规律测试更多资源系列卫星
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'satelliteTool'))

from get_TLE_data import get_tle
import time

def test_ziyuan_pattern():
    """基于成功的命名模式测试"""
    
    # 成功的模式:
    # ZIYUAN 1-02C -> ZIYUAN 1-02C (ZY 1-02C)
    # ZIYUAN 3 -> ZIYUAN 3-1 (ZY 3-1)
    
    # 基于这个模式尝试更多变体
    ziyuan_variants = [
        # 资源一号系列 - 02X 模式
        "ZIYUAN 1-02A",
        "ZIYUAN 1-02B", 
        "ZIYUAN 1-02C",  # 已知成功
        "ZIYUAN 1-02D",
        "ZIYUAN 1-02E",
        "ZIYUAN 1-02F",
        
        # 资源三号系列 - 数字模式  
        "ZIYUAN 3",      # 已知成功
        "ZIYUAN 3-1",
        "ZIYUAN 3-2", 
        "ZIYUAN 3-3",
        "ZIYUAN 3-01",
        "ZIYUAN 3-02",
        "ZIYUAN 3-03",
        
        # 其他可能的模式
        "ZIYUAN 1",
        "ZIYUAN 1-01A",
        "ZIYUAN 1-01B",
        "ZIYUAN 1-01C",
        "ZIYUAN 1-03A",
        "ZIYUAN 1-03B",
        
        # 资源二号？
        "ZIYUAN 2",
        "ZIYUAN 2-1",
        "ZIYUAN 2-01",
        
        # 简化版本
        "ZY 1-02A",
        "ZY 1-02B",
        "ZY 1-02C",
        "ZY 1-02D", 
        "ZY 1-02E",
        "ZY 3-1",
        "ZY 3-2",
        "ZY 3-3"
    ]
    
    print("🛰️ 基于成功模式测试资源系列卫星")
    print("="*45)
    print("参考成功模式:")
    print("✅ ZIYUAN 1-02C -> ZIYUAN 1-02C (ZY 1-02C)")
    print("✅ ZIYUAN 3 -> ZIYUAN 3-1 (ZY 3-1)")
    print("="*45)
    
    success = {}
    
    for sat in ziyuan_variants:
        print(f"测试: {sat}")
        try:
            tle = get_tle(sat)
            if isinstance(tle, str) and "No GP data found" not in tle and "Error" not in tle:
                lines = tle.split('\n')
                if len(lines) >= 3:
                    actual_name = lines[0].strip()
                    print(f"  ✅ 成功! -> {actual_name}")
                    success[sat] = actual_name
                else:
                    print(f"  ❌ 数据不完整")
            else:
                print(f"  ❌ 未找到")
        except Exception as e:
            print(f"  ❌ 错误: {e}")
        
        time.sleep(0.1)
    
    print(f"\n📊 测试结果:")
    print(f"总测试: {len(ziyuan_variants)}个")
    print(f"成功: {len(success)}个")
    
    if success:
        print(f"\n✅ 所有找到的资源系列卫星:")
        for i, (query, actual) in enumerate(success.items(), 1):
            print(f"{i:2d}. {query} -> {actual}")
            
        # 分析命名规律
        print(f"\n🔍 命名规律分析:")
        for query, actual in success.items():
            if "1-02" in query:
                print(f"资源一号02系列: {query} -> {actual}")
            elif "3" in query:
                print(f"资源三号系列: {query} -> {actual}")
            else:
                print(f"其他系列: {query} -> {actual}")
    else:
        print("\n❌ 除了已知的2个，未找到其他资源系列卫星")

if __name__ == "__main__":
    test_ziyuan_pattern()
