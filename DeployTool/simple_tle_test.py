"""
简单的TLE数据获取测试
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'satelliteTool'))

from get_TLE_data import get_tle

def test_iss():
    """测试ISS TLE获取"""
    print("测试ISS...")
    tle = get_tle("ISS (ZARYA)")
    if "ISS" in tle and len(tle.split('\n')) >= 3:
        print("✅ ISS TLE获取成功")
        return True
    else:
        print("❌ ISS TLE获取失败")
        return False

def test_gaofen():
    """测试高分卫星TLE获取"""
    satellites = ["GAOFEN-1", "GAOFEN-2", "GAOFEN-3", "GAOFEN-4"]
    success_count = 0
    
    print("测试高分系列...")
    for sat in satellites:
        tle = get_tle(sat)
        if isinstance(tle, str) and "No GP data found" not in tle and "Error" not in tle:
            if len(tle.split('\n')) >= 3:
                print(f"✅ {sat} 成功")
                success_count += 1
            else:
                print(f"❌ {sat} 数据不完整")
        else:
            print(f"❌ {sat} 未找到")
    
    print(f"高分系列成功: {success_count}/{len(satellites)}")
    return success_count

def main():
    print("=== 简单TLE测试 ===")
    
    # 测试ISS
    iss_ok = test_iss()
    
    # 测试高分系列
    gf_count = test_gaofen()
    
    print(f"\n结果汇总:")
    print(f"ISS: {'成功' if iss_ok else '失败'}")
    print(f"高分系列: {gf_count}个成功")

if __name__ == "__main__":
    main()
