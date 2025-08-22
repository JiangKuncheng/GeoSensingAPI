import geojson
from skyfield.api import EarthSatellite, Loader
from datetime import datetime, timedelta
import math
from shapely.geometry import Point, mapping
from shapely.ops import transform
from pyproj import Proj, Transformer
from pytz import utc

from satelliteTool.find_Satellite import get_valid_satellite_tle_as_dict


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
			satellite_features[name] = geojson.FeatureCollection(features_for_satellite)

	return satellite_features


if __name__ == '__main__':
	# --- 1. 定义包含所有卫星TLE的字典 ---
	database_file = 'D:\GeoSensingAPI\data\satellite_data.db'
	tle_data_dict = get_valid_satellite_tle_as_dict(database_file)

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