import geojson
from skyfield.api import EarthSatellite, Loader
from datetime import datetime, timedelta
import math
import os
from shapely.geometry import Point, mapping
from shapely.ops import transform
from pyproj import Proj, Transformer
from pytz import utc
from typing import Union, List, Dict

from satelliteTool.get_TLE_data import get_tle

# 确保保存目录存在
SAVE_DIR = "./geojson"
os.makedirs(SAVE_DIR, exist_ok=True)



def get_observation_lace(
		satellite_names: Union[str, List[str]],
		start_time_str: str,
		end_time_str: str,
		fov: float = 10.0,
		interval_seconds: int = 300
) -> Union[str, Dict[str, str]]:
	"""
	获取一个或多个卫星的观测轨迹并保存为GeoJSON文件。
	
	参数:
		satellite_names (Union[str, List[str]]): 
			单个卫星名称（字符串），或多个卫星名称组成的列表。
		start_time_str (str): 观测开始时间的字符串 (例如 "2025-08-01 00:00:00.000")。
		end_time_str (str): 观测结束时间的字符串 (例如 "2025-08-01 23:59:59.000")。
		fov (float): 卫星的视场角 (Field of View)，单位是度。默认为 10.0。
		interval_seconds (int): 计算轨迹点的时间间隔，单位是秒。默认为 300 (5分钟)。
	
	返回:
		Union[str, Dict[str, str]]:
			- 如果传入单个名称，返回对应的GeoJSON文件名（不含路径）。
			- 如果传入多个名称，返回字典，键为卫星名称，值为对应的GeoJSON文件名（不含路径）。
			- 文件实际保存在 ./geojson/ 目录下。
	"""
	# 如果是单个字符串，转为列表处理
	is_single = isinstance(satellite_names, str)
	names = [satellite_names] if is_single else satellite_names
	
	# 获取TLE数据
	tle_data = get_tle(names)
	if is_single:
		tle_data = {satellite_names: tle_data}
	
	# 准备TLE字典，格式化为三行格式
	tle_dict = {}
	for name, tle_str in tle_data.items():
		if isinstance(tle_str, str) and not tle_str.startswith("Error") and not tle_str.startswith("Exception") and tle_str.strip():
			# 添加卫星名作为第0行
			tle_dict[name] = f"{name}\n{tle_str}"
	
	if not tle_dict:
		error_msg = "No valid TLE data found"
		return error_msg if is_single else {name: error_msg for name in names}
	
	# 计算覆盖轨迹
	coverage_results = {}
	
	# 优化：在函数作用域内只加载一次 timescale
	load = Loader('~/skyfield-data', verbose=False)
	ts = load.timescale()

	for name, tle_lines_str in tle_dict.items():
		print(f"---> 正在处理卫星: {name}")
		features_for_satellite = []

		# --- 核心修改：为每个卫星添加独立的异常处理块 ---
		try:
			# 1. 解析TLE和时间
			try:
				lines = tle_lines_str.strip().split('\n')
				if len(lines) >= 3:
					# 三行格式：卫星名、TLE第一行、TLE第二行
					tle_line1, tle_line2 = lines[1].strip(), lines[2].strip()
				elif len(lines) == 2:
					# 两行格式：TLE第一行、TLE第二行
					tle_line1, tle_line2 = lines[0].strip(), lines[1].strip()
				else:
					raise ValueError("TLE 格式无效")
			except (ValueError, IndexError):
				raise ValueError("TLE 格式无效，必须是包含换行符的TLE字符串。")

			satellite = EarthSatellite(tle_line1, tle_line2, name, ts)

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
			coverage_results[name] = geojson.FeatureCollection(features_for_satellite)
	
	# 保存结果并返回文件名
	results = {}
	for name in names:
		if name in coverage_results:
			# 生成文件名
			safe_name = name.replace(' ', '_').replace('/', '_')
			filename = f"{safe_name}_observation_lace.geojson"
			file_path = os.path.join(SAVE_DIR, filename)
			
			try:
				# 保存GeoJSON文件
				with open(file_path, 'w', encoding='utf-8') as f:
					geojson.dump(coverage_results[name], f, indent=2)
				results[name] = filename  # 只返回文件名，不包含路径
			except Exception as e:
				results[name] = f"Error saving file: {e}"
		else:
			results[name] = "No coverage data generated"
	
	return results[satellite_names] if is_single else results


if __name__ == '__main__':
	# --- 测试新的API ---
	satellite_name = "LANDSAT 8"
	start_time = "2025-08-01 00:00:00.000"
	end_time = "2025-08-01 23:59:59.000"
	
	print(f"--- 测试获取 {satellite_name} 的观测轨迹 ---")
	result = get_observation_lace(
		satellite_names=satellite_name,
		start_time_str=start_time,
		end_time_str=end_time,
		fov=15.0,
		interval_seconds=600
	)
	print(f"结果: {result}")
	
	# --- 测试多个卫星 ---
	satellite_names = ["LANDSAT 8", "LANDSAT 9"]
	print(f"\n--- 测试获取多个卫星的观测轨迹 ---")
	results = get_observation_lace(
		satellite_names=satellite_names,
		start_time_str=start_time,
		end_time_str=end_time,
		fov=15.0,
		interval_seconds=600
	)
	print(f"结果: {results}")
	
	print(f"\n--- 函数更新完成，统一使用新接口 ---")