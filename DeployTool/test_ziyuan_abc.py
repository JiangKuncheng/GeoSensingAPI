"""
测试资源系列卫星ABC命名规范
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'satelliteTool'))

from get_TLE_data import get_tle
import time

def test_ziyuan_abc():
    """测试资源系列ABC命名"""
    
    # 资源系列ABC命名
    ziyuan_abc = [
        # 资源一号系列
        "ZIYUAN 1A",
        "ZIYUAN 1B", 
        "ZIYUAN 1C",
        "ZIYUAN 1D",
        "ZIYUAN 1E",
        "ZIYUAN 1F",
        "ZIYUAN-1A",
        "ZIYUAN-1B",
        "ZIYUAN-1C",
        "ZIYUAN-1D", 
        "ZIYUAN-1E",
        "ZIYUAN-1F",
        
        # 资源三号系列
        "ZIYUAN 3A",
        "ZIYUAN 3B",
        "ZIYUAN 3C",
        "ZIYUAN-3A",
        "ZIYUAN-3B", 
        "ZIYUAN-3C",
        
        # 简化命名
        "ZY-1A",
        "ZY-1B",
        "ZY-1C",
        "ZY-1D",
        "ZY-1E", 
        "ZY-1F",
        "ZY-3A",
        "ZY-3B",
        "ZY-3C"
    ]
    
    print("🛰️ 资源系列ABC命名测试")
    print("="*40)
    
    success = {}
    
    for sat in ziyuan_abc:
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
    
    print(f"\n📊 ABC命名测试结果:")
    print(f"总测试: {len(ziyuan_abc)}个")
    print(f"成功: {len(success)}个")
    
    if success:
        print(f"\n✅ 找到的资源系列卫星:")
        for i, (query, actual) in enumerate(success.items(), 1):
            print(f"{i:2d}. {query} -> {actual}")
    else:
        print("\n❌ 未找到任何ABC命名的资源系列卫星")

if __name__ == "__main__":
    test_ziyuan_abc()
