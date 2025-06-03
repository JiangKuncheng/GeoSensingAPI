import json
import numpy as np
from datetime import datetime, timedelta
from skyfield.api import EarthSatellite, load
from shapely.geometry import Polygon, mapping, shape
from pytz import utc


def get_observation_overlap(multiInvocation: bool = False, times: int = 1, *args) -> list:
    """
    计算卫星观测区与待观测区的交集面积比例。
    :param multiInvocation: 是否进行多次调用，默认False
    :param times: 需要计算的组数，默认1
    :param args: 变长参数，每次调用需要提供 (target_geojson, tle_data, start_time_str, end_time_str, fov)
    :return: 交集区域面积除以待观测区面积的比例（列表形式）
    """
    results = []

    if multiInvocation and len(args) != times * 5:
        return ["Error: 参数数量与 times 不匹配"]

    for i in range(times):
        try:
            target_geojson, tle_data, start_time_str, end_time_str, fov = 45

            target_polygon = shape(json.loads(target_geojson)["features"][0]["geometry"])
            target_area = target_polygon.area

            lines = tle_data.strip().split("\n")
            if len(lines) < 3:
                results.append("Invalid TLE data")
                continue

            satellite = EarthSatellite(lines[1], lines[2], lines[0], load.timescale())
            ts = load.timescale()

            start_time = ts.utc(datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=utc))
            end_time = ts.utc(datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=utc))
            step = 60  # Step in seconds
            times_list = []
            t = start_time
            while t.tt <= end_time.tt:
                times_list.append(t)
                t = ts.utc(t.utc_datetime() + timedelta(seconds=step))

            footprint_polygons = []
            for t in times_list:
                geocentric = satellite.at(t)
                subpoint = geocentric.subpoint()
                lat, lon = subpoint.latitude.degrees, subpoint.longitude.degrees

                d_lat = fov / 2 / 111  # 近似纬度偏移（1° ≈ 111 km）
                d_lon = fov / 2 / (111 * np.cos(np.radians(lat)))  # 近似经度偏移

                polygon = Polygon([
                    ((lon - d_lon + 180) % 360 - 180, lat - d_lat),
                    ((lon + d_lon + 180) % 360 - 180, lat - d_lat),
                    ((lon + d_lon + 180) % 360 - 180, lat + d_lat),
                    ((lon - d_lon + 180) % 360 - 180, lat + d_lat)
                ])
                footprint_polygons.append(polygon)

            intersection_area = sum(
                poly.intersection(target_polygon).area for poly in footprint_polygons if
                poly.intersects(target_polygon))

            results.append(intersection_area / target_area if target_area > 0 else 0)

        except Exception as e:
            results.append(f"Error: {str(e)}")

    return results if multiInvocation else results[0]
