import geojson
import json
import os
from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta
import math
from typing import List, Dict, Union


def get_coverage_lace(satellite_configs: Union[Dict, List[Dict]]) -> Dict[str, str]:
    """
    计算卫星视场角覆盖的地面区域并保存为 GeoJSON 文件。

    参数:
        satellite_configs (Union[Dict, List[Dict]]): 
            单个卫星配置字典或配置字典列表，每个配置包含：
            {
                "tle_str": "TLE数据字符串",
                "start_time_str": "开始时间",
                "end_time_str": "结束时间", 
                "interval": 时间间隔(秒),
                "fov": 视场角(度),
                "output_path": "输出文件路径"
            }

    返回:
        Dict[str, str]: 键为output_path，值为处理结果状态
    """
    # 确保data目录存在
    os.makedirs("data", exist_ok=True)
    
    ts = load.timescale()
    
    # 统一处理为列表格式
    configs = [satellite_configs] if isinstance(satellite_configs, dict) else satellite_configs
    
    results = {}

    for config in configs:
        tle_str = config["tle_str"]
        start_time_str = config["start_time_str"] 
        end_time_str = config["end_time_str"]
        interval = config["interval"]
        fov = config["fov"]
        output_path = config["output_path"]
        try:
            all_features = []
            
            lines = tle_str.strip().split('\n')
            name = lines[0].strip()
            tle_line1 = lines[1].strip()
            tle_line2 = lines[2].strip()

            satellite = EarthSatellite(tle_line1, tle_line2, name, ts)

            start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f")

            current_time = start_time
            observation_count = 0
            
            while current_time <= end_time:
                t = ts.utc(current_time.year, current_time.month, current_time.day,
                           current_time.hour, current_time.minute, current_time.second)
                geocentric = satellite.at(t)
                subpoint = geocentric.subpoint()
                lon, lat = subpoint.longitude.degrees, subpoint.latitude.degrees

                # 计算视场角形成的覆盖区域（改进算法）
                # 地球半径 6371km，将视场角转换为地表覆盖半径
                earth_radius = 6371.0
                satellite_altitude = geocentric.distance().km - earth_radius
                
                # 根据卫星高度和视场角计算地表覆盖半径
                if satellite_altitude > 0:
                    coverage_radius_deg = math.degrees(math.atan(
                        satellite_altitude * math.tan(math.radians(fov / 2)) / earth_radius
                    ))
                else:
                    coverage_radius_deg = fov / 111.0  # 简单近似：1度约111km
                
                # 生成覆盖区域多边形（圆形近似）
                circle_points = []
                for angle in range(0, 361, 15):  # 每15度一个点，减少数据量
                    angle_rad = math.radians(angle)
                    point_lon = lon + coverage_radius_deg * math.cos(angle_rad)
                    point_lat = lat + coverage_radius_deg * math.sin(angle_rad)
                    
                    # 确保经纬度在有效范围内
                    point_lon = max(-180, min(180, point_lon))
                    point_lat = max(-90, min(90, point_lat))
                    
                    circle_points.append([point_lon, point_lat])
                
                # 闭合多边形
                circle_points.append(circle_points[0])

                coverage_polygon = geojson.Polygon([circle_points])

                feature = geojson.Feature(
                    geometry=coverage_polygon,
                    properties={
                        "satellite": name,
                        "timestamp": current_time.isoformat(),
                        "observation_id": observation_count,
                        "satellite_altitude_km": satellite_altitude,
                        "coverage_radius_deg": coverage_radius_deg,
                        "longitude": lon,
                        "latitude": lat
                    }
                )
                all_features.append(feature)
                observation_count += 1

                current_time += timedelta(seconds=interval)

            # 创建FeatureCollection
            coverage_geojson = geojson.FeatureCollection(all_features)
            
            # 保存到文件
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(coverage_geojson, f, ensure_ascii=False, indent=2)
            
            results[output_path] = f"成功: {name} 生成 {observation_count} 个观测点"
            
        except Exception as e:
            results[output_path] = f"错误: {tle_str[:20]}... - {str(e)}"
    
    return results


if __name__ == '__main__':
    tle = """ISS (ZARYA)             
    1 25544U 98067A   25073.85652051  .00016840  00000+0  30216-3 0  9992
    2 25544  51.6358  54.2440 0006407  21.9595 338.1668 15.50010161500535"""

    print(get_coverage_lace(tle, "2025-03-04 12:00:00.000", "2025-03-04 12:30:00.000"))