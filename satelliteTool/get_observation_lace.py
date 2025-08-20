import geojson
from skyfield.api import EarthSatellite, Loader, Timescale
from datetime import datetime, timedelta
import math
from shapely.geometry import Point, mapping
from shapely.ops import transform
from pyproj import Proj, Transformer
from pytz import utc


def get_coverage_lace(
		tle_dict: dict,
		start_time_str: str,
		end_time_str: str,
		fov: float = 10.0,
		interval_seconds: int = 300
) -> dict:
	"""
    计算多个卫星在指定时间段内的地面覆盖轨迹，并返回一个字典。
    函数现在更健壮，能够处理无效的TLE数据而不会中断。

    :param tle_dict: 一个字典，键是卫星名称(str)，值是两行的TLE字符串(str)。
    :param start_time_str: 观测开始时间的字符串 (例如 "2025-08-01 00:00:00.000")。
    :param end_time_str: 观测结束时间的字符串 (例如 "2025-08-01 23:59:59.000")。
    :param fov: 卫星的视场角 (Field of View)，单位是度。默认为 10.0。
    :param interval_seconds: 计算轨迹点的时间间隔，单位是秒。默认为 300 (5分钟)。
    :return: 字典，键为卫星名称，值为对应的GeoJSON FeatureCollection。
    """
	# 优化：在函数作用域内只加载一次 timescale
	# 指定一个目录来缓存下载的星历文件，避免每次都在当前目录下载
	load = Loader('~/skyfield-data', verbose=False)
	ts = load.timescale()

	satellite_features = {}

	for name, tle_lines_str in tle_dict.items():
		print(f"---> 正在处理卫星: {name}")
		features_for_satellite = []

		# --- 核心修改：为每个卫星添加独立的异常处理块 ---
		try:
			# 1. 解析TLE和时间
			try:
				tle_line1, tle_line2 = tle_lines_str.strip().split('\n')
			except ValueError:
				raise ValueError("TLE 格式无效，必须是包含换行符的两行字符串。")

			satellite = EarthSatellite(tle_line1.strip(), tle_line2.strip(), name, ts)

			# 检查卫星轨道是否已衰退
			if satellite.model.error != 0:
				raise ValueError(f"TLE数据显示轨道根数错误或已衰退: {satellite.model.error_message}")

			start_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=utc)
			end_dt = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=utc)

			# 2. 创建时间点数组
			time_points = []
			current_dt = start_dt
			while current_dt <= end_dt:
				time_points.append(current_dt)
				current_dt += timedelta(seconds=interval_seconds)

			if not time_points:
				print(f"!!! 警告: '{name}' 的时间范围无效，跳过。")
				continue

			t_skyfield = ts.from_datetimes(time_points)

			# 3. 轨道计算（这是最容易出错的步骤）
			geocentric = satellite.at(t_skyfield)
			subpoint = geocentric.subpoint()

			# 4. 循环生成每个精确的足迹
			for i in range(len(time_points)):
				lon = subpoint.longitude.degrees[i]
				lat = subpoint.latitude.degrees[i]
				alt_km = subpoint.elevation.km[i]

				# 如果高度为非正数，说明卫星已再入大气层，跳过
				if alt_km <= 0:
					continue

				coverage_radius_km = alt_km * math.tan(math.radians(fov / 2))

				# 使用WGS 84球体模型进行投影计算
				local_proj = Proj(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84 +units=m")
				wgs84_proj = Proj('epsg:4326')  # WGS 84 经纬度

				to_local_transformer = Transformer.from_proj(wgs84_proj, local_proj, always_xy=True)
				from_local_transformer = Transformer.from_proj(local_proj, wgs84_proj, always_xy=True)

				center_point_local = transform(to_local_transformer.transform, Point(lon, lat))
				buffer_local = center_point_local.buffer(coverage_radius_km * 1000)  # 转换为米

				footprint_polygon_geom = transform(from_local_transformer.transform, buffer_local)

				feature = geojson.Feature(
					geometry=mapping(footprint_polygon_geom),
					properties={"satellite": name, "timestamp": time_points[i].isoformat()}
				)
				features_for_satellite.append(feature)

		# --- 捕获所有可能的错误 ---
		except Exception as e:
			# 打印详细错误，方便调试
			print(f"!!! 错误: 处理 '{name}' 时失败: {e}")
			# 即使出错，也继续处理下一个卫星

		finally:
			# --- 无论成功还是失败，都为该卫星创建一个条目 ---
			# 这样可以确保返回的字典中包含所有请求的卫星
			# 成功的卫星将有features，失败的将是一个空的features列表
			satellite_features[name] = geojson.FeatureCollection(features_for_satellite)

	return satellite_features


if __name__ == '__main__':
	# ... (你的主函数代码无需修改) ...
	# --- 1. 定义包含所有卫星TLE的字典 ---
	tle_data_dict = {
		"LANDSAT 9": "1 49260U 21088A   25225.90087331  .00000343  00000-0  86120-4 0  9998\n2 49260  98.2240 295.6621 0001152  92.7233 267.4097 14.57102349206250",
		"LANDSAT 8": "1 39084U 13008A   25225.93518726  .00000330  00000-0  83304-4 0  9991\n2 39084  98.2219 295.6904 0001221  90.8808 269.2530 14.57106224653150",
		"LANDSAT 7": "1 25682U 99020A   25225.96558631  .00000447  00000-0  94797-4 0  9997\n2 25682  97.8629 238.7471 0001408  78.5884 338.4838 14.63487946400903",
		"SENTINEL 2A": "1 40697U 15028A   25225.66220237  .00000108  00000-0  57680-4 0  9995\n2 40697  98.5664 299.9242 0001176  96.3963 263.7354 14.30826489529757",
		"SENTINEL 2B": "1 42063U 17013A   25225.93481032  .00000105  00000-0  56678-4 0  9995\n2 42063  98.5667 300.1355 0001261  95.8035 264.3292 14.30816795440702",
		"GAOFEN 6": "1 43484U 18048A   25225.89293148  .00000671  00000-0  10323-3 0  9990\n2 43484  97.8191 294.0983 0013707  87.9596 272.3184 14.76540806388048",
		"GAOFEN 1": "1 39150U 13018A   25225.93920346  .00000655  00000-0  10102-3 0  9996\n2 39150  97.9464 298.6386 0017702 171.2539 188.8983 14.76544463662908",
		"GAOFEN 1-02": "1 43259U 18031A   25225.89168981  .00000725  00000-0  11078-3 0  9996\n2 43259  97.7680 284.7617 0003750 264.3203  95.7580 14.76606704397354",
		"GAOFEN 1-03": "1 43260U 18031B   25225.93764942  .00000729  00000-0  11133-3 0  9998\n2 43260  97.7673 284.6950 0004656 311.5203  48.5607 14.76597261397351",
		"GAOFEN 1-04": "1 43262U 18031D   25225.91328914  .00000762  00000-0  11606-3 0  9995\n2 43262  97.7683 284.8258 0000988 345.8113  14.3069 14.76592202397343",
		"ZY-1 02E": "1 50465U 21131A   25225.87772090  .00000088  00000-0  45734-4 0  9997\n2 50465  98.4746 304.0172 0000690  26.8277 333.2944 14.35385677190337",
		"ZY-1 02D": "1 44528U 19059A   25225.87992434  .00000114  00000-0  54421-4 0  9995\n2 44528  98.3636 292.5392 0001232  21.9608 338.1630 14.35428680310252",
		"HJ-2F": "1 57519U 23116A   25225.95114683  .00009067  00000-0  38847-3 0  9998\n2 57519  97.3875 231.8057 0003349  45.7676 314.3835 15.22989263112039",
		"HJ-2E": "1 54035U 22132A   25225.91830765  .00009062  00000-0  38767-3 0  9993\n2 54035  97.3819 231.1366 0006806  21.0137 339.1378 15.23025509157696",
		"HJ-2B": "1 46479U 20067B   25225.94525504  .00000704  00000-0  10824-3 0  9994\n2 46479  97.9164 306.9150 0000744  73.7489 286.3803 14.76529418262923",
		"HJ-2A": "1 46478U 20067A   25225.90911622  .00000719  00000-0  11039-3 0  9994\n2 46478  97.9112 306.0764 0003417 141.3878 218.7577 14.76528696262914"
	}

	start_time = "2025-08-01 00:00:00.000"
	end_time = "2025-08-01 23:59:59.000"
	field_of_view = 10.0
	time_interval = 600

	print(f"--- 开始计算 {len(tle_data_dict)} 颗卫星的覆盖范围 ---")
	print(f"时间范围: {start_time} to {end_time}")

	coverage_dict = get_coverage_lace(
		tle_dict=tle_data_dict,
		start_time_str=start_time,
		end_time_str=end_time,
		fov=field_of_view,
		interval_seconds=time_interval
	)

	total_features = sum(len(geojson['features']) for geojson in coverage_dict.values())
	print(f"\n--- 计算完成，总共生成了 {total_features} 个足迹。 ---")
	print(f"--- 涉及 {len(coverage_dict)} 颗卫星 ---")

	output_filename = "satellite_coverage_2025-08-01.json"
	try:
		with open(output_filename, 'w') as f:
			geojson.dump(coverage_dict, f, indent=2)
		print(f"✅ 结果已成功保存到文件: {output_filename}")
	except Exception as e:
		print(f"❌ 保存文件时出错: {e}")