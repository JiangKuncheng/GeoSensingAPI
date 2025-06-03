import requests

BASE_URL = "http://localhost:8001"

def test_get_boundary():
    url = f"{BASE_URL}/get_boundary"
    payload = {
        "place_names": ["Wuhan", "Shanghai", "New York"]
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("边界 GeoJSON 路径:", data)
    return data["data"]

def test_area(geojson_paths):
    url = f"{BASE_URL}/area"
    payload = {
        "geojson_paths": list(geojson_paths.values())  # 传入多个路径列表
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("面积计算结果:", data)
    return data["areas"]

def test_get_tle():
    url = f"{BASE_URL}/get_tle"
    payload = {
        "satellite_names": ["ISS (ZARYA)", "NOAA 19", "TERRA"]
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("TLE 数据:", data)
    return data["data"]

def test_calculate_velocity(tle_dict):
    url = f"{BASE_URL}/calculate_velocity"
    payload = {
        "tle_dict": tle_dict
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    print("速度计算结果:", data)
    return data["velocities"]

if __name__ == "__main__":
    print("=== 获取边界 ===")
    boundaries = test_get_boundary()
    print("\n=== 计算面积 ===")
    areas = test_area(boundaries)
    print("\n=== 获取卫星 TLE ===")
    tle_data = test_get_tle()
    print("\n=== 计算轨道速度 ===")
    velocities = test_calculate_velocity(tle_data)
