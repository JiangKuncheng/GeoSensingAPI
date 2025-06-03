import geojson
from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta
import math


def get_coverage_lace(multiInvocation=False, times=1, *args):
    """
    计算卫星视场角覆盖的地面区域并返回 GeoJSON 格式。

    :param multiInvocation: 是否进行多次调用，默认 False
    :param times: 调用次数（当 multiInvocation 为 True 时生效）
    :param args: 变长参数，每组参数包括（tle_str, start_time_str, end_time_str, interval, fov）
    :return: GeoJSON 格式的覆盖区域数据
    """
    ts = load.timescale()
    all_features = []

    if multiInvocation:
        if len(args) != times * 5:
            raise ValueError("参数数量与 times 指定的次数不匹配")

        param_sets = [args[i:i + 5] for i in range(0, len(args), 5)]
    else:
        if len(args) != 5:
            raise ValueError("单次调用时需要提供 5 个参数")
        param_sets = [args]

    for tle_str, start_time_str, end_time_str, interval, fov in param_sets:
        lines = tle_str.strip().split('\n')
        name = lines[0].strip()
        tle_line1 = lines[1].strip()
        tle_line2 = lines[2].strip()

        satellite = EarthSatellite(tle_line1, tle_line2, name, ts)

        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f")

        current_time = start_time
        while current_time <= end_time:
            t = ts.utc(current_time.year, current_time.month, current_time.day,
                       current_time.hour, current_time.minute, current_time.second)
            geocentric = satellite.at(t)
            subpoint = geocentric.subpoint()
            lon, lat = subpoint.longitude.degrees, subpoint.latitude.degrees

            # 计算视场角形成的覆盖区域（近似圆形）
            coverage_radius = 6371 * math.radians(fov / 2)  # 近似计算地表覆盖半径（km）

            coverage_polygon = geojson.Polygon([
                [
                    (lon + coverage_radius * math.cos(math.radians(angle)),
                     lat + coverage_radius * math.sin(math.radians(angle)))
                    for angle in range(0, 361, 10)
                ]
            ])

            feature = geojson.Feature(
                geometry=coverage_polygon,
                properties={"satellite": name, "timestamp": current_time.isoformat()}
            )
            all_features.append(feature)

            current_time += timedelta(seconds=interval)

    return geojson.FeatureCollection(all_features)


if __name__ == '__main__':
    tle = """ISS (ZARYA)             
    1 25544U 98067A   25073.85652051  .00016840  00000+0  30216-3 0  9992
    2 25544  51.6358  54.2440 0006407  21.9595 338.1668 15.50010161500535"""

    print(get_coverage_lace(tle, "2025-03-04 12:00:00.000", "2025-03-04 12:30:00.000"))