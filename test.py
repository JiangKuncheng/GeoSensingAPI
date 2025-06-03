from skyfield.api import load, EarthSatellite
from datetime import datetime, timedelta
import geojson


def tle_to_geojson(tle_str, start_time_str, end_time_str, interval=10):
    """
    计算卫星轨迹投影到地球表面的 GeoJSON

    :param tle_str: TLE 数据字符串，按格式传入
    :param start_time_str: 开始时间（格式：YYYY-MM-DD HH:MM:SS.sss）
    :param end_time_str: 结束时间（格式：YYYY-MM-DD HH:MM:SS.sss）
    :param interval: 采样间隔（秒）
    :return: GeoJSON 格式的轨迹数据
    """
    ts = load.timescale()
    lines = tle_str.strip().split('\n')

    name = lines[0].strip()
    tle_line1 = lines[1].strip()
    tle_line2 = lines[2].strip()

    satellite = EarthSatellite(tle_line1, tle_line2, name, ts)

    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f")
    end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f")

    points = []
    current_time = start_time
    while current_time <= end_time:
        t = ts.utc(current_time.year, current_time.month, current_time.day,
                   current_time.hour, current_time.minute, current_time.second)
        geocentric = satellite.at(t)
        subpoint = geocentric.subpoint()
        points.append((subpoint.longitude.degrees, subpoint.latitude.degrees))
        current_time += timedelta(seconds=interval)

    # 创建 GeoJSON 线条特征
    feature = geojson.Feature(
        geometry=geojson.LineString(points),
        properties={"satellite": name}
    )

    return geojson.FeatureCollection([feature])


if __name__ == '__main__':
    tle="""ISS (ZARYA)             
1 25544U 98067A   25073.85652051  .00016840  00000+0  30216-3 0  9992
2 25544  51.6358  54.2440 0006407  21.9595 338.1668 15.50010161500535"""

    print(tle_to_geojson(tle,"2025-03-04 12:00:00.000","2025-03-04 12:30:00.000"))