# -*- coding: utf-8 -*-

import os
import math
import sys
import json
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon, LineString, Point, MultiPoint
from shapely.ops import unary_union, voronoi_diagram
from sklearn.cluster import KMeans
import numpy as np
import folium
import matplotlib.pyplot as plt


# ==============================================================================
# 1. 辅助函数 (Helper Functions) - 无需修改
# ==============================================================================
def create_wuhan_geojson(file_path="wuhan_east_lake.geojson"):
	if os.path.exists(file_path):
		print(f"文件 '{file_path}' 已存在，将使用现有文件。")
		return
	print(f"正在创建虚拟GeoJSON文件: '{file_path}'")
	polygon_geom = Polygon([
		(114.3948, 30.5488), (114.4102, 30.5594), (114.4208, 30.5458),
		(114.4033, 30.5365), (114.3948, 30.5488)
	])
	gdf = gpd.GeoDataFrame(geometry=[polygon_geom], crs="EPSG:4326")
	gdf.to_file(file_path, driver='GeoJSON')
	print("虚拟GeoJSON文件创建成功。")


def get_utm_crs(gdf_latlon):
	centroid = gdf_latlon.unary_union.centroid
	lon, lat = centroid.x, centroid.y
	utm_band = str(int((lon + 180) // 6 + 1))
	if lat >= 0:
		epsg_code = '326' + utm_band.zfill(2)
	else:
		epsg_code = '327' + utm_band.zfill(2)
	return f"EPSG:{epsg_code}"


def generate_s_path_in_polygon(polygon: Polygon, swath_width: float) -> (LineString, float):
	if polygon.is_empty or polygon.area == 0: return None, 0
	mbr = polygon.minimum_rotated_rectangle
	if mbr.is_empty: return None, 0
	x, y = mbr.exterior.coords.xy
	edge_lengths = (Point(x[0], y[0]).distance(Point(x[1], y[1])), Point(x[1], y[1]).distance(Point(x[2], y[2])))
	long_edge_start_pt = (Point(x[0], y[0]), Point(x[1], y[1])) if edge_lengths[0] > edge_lengths[1] else (
	Point(x[1], y[1]), Point(x[2], y[2]))
	angle_rad = math.atan2(long_edge_start_pt[1].y - long_edge_start_pt[0].y,
	                       long_edge_start_pt[1].x - long_edge_start_pt[0].x)
	rotated_poly = gpd.GeoSeries(polygon).rotate(-math.degrees(angle_rad), origin=(0, 0)).iloc[0]
	min_x, min_y, max_x, max_y = rotated_poly.bounds
	scan_lines_coords = []
	y_current = min_y + swath_width / 2
	direction = 1
	while y_current <= max_y:
		line = LineString([(min_x - 10, y_current), (max_x + 10, y_current)])
		intersected = rotated_poly.intersection(line)
		if not intersected.is_empty:
			if intersected.geom_type == 'MultiLineString':
				geoms = sorted(list(intersected.geoms), key=lambda ls: ls.coords[0][0], reverse=(direction == -1))
				for g in geoms: scan_lines_coords.append(list(g.coords))
			elif intersected.geom_type == 'LineString':
				coords = list(intersected.coords)
				if direction == -1: coords.reverse()
				scan_lines_coords.append(coords)
		y_current += swath_width
		direction *= -1
	if not scan_lines_coords: return None, 0
	path_points = []
	for i, coords in enumerate(scan_lines_coords):
		path_points.extend(coords)
		if i < len(scan_lines_coords) - 1: path_points.append(scan_lines_coords[i + 1][0])
	if not path_points: return None, 0
	final_path_rotated = LineString(path_points)
	final_path = gpd.GeoSeries(final_path_rotated).rotate(math.degrees(angle_rad), origin=(0, 0)).iloc[0]
	return final_path, final_path.length


# ==============================================================================
# 2. 主规划器类 (Main Planner Class)
# ==============================================================================
class MultiUAVPlanner:
	def __init__(self, geojson_path: str, uavs_params: list):
		print("--- 初始化多无人机规划器 ---")
		self.uavs = uavs_params
		self.num_uavs = len(uavs_params)
		print(f"加载区域文件: {geojson_path}")
		self.area_gdf_latlon = gpd.read_file(geojson_path).to_crs("EPSG:4326")
		self.original_crs = self.area_gdf_latlon.crs
		self.utm_crs = get_utm_crs(self.area_gdf_latlon)
		print(f"原始坐标系: {self.original_crs}. 内部计算将使用自动选择的UTM坐标系: {self.utm_crs}")
		self.area_gdf_utm = self.area_gdf_latlon.to_crs(self.utm_crs)
		self.total_area_shape_utm = self.area_gdf_utm.unary_union
		self.results = []
		self.coverage_percentage = 0.0

	# ====================================================================
	# === 【新增功能 1】可行性预检查 ===
	# ====================================================================
	def pre_check_feasibility(self):
		"""在规划前，快速估算整个机队理论上能否覆盖目标区域"""
		print("\n--- 执行可行性预检查 ---")
		total_area_needed = self.total_area_shape_utm.area

		total_max_coverage_capability = 0
		for uav in self.uavs:
			# 理论最大覆盖面积 = 速度 * 时间 * 宽度 (不考虑转弯等损耗)
			max_area_per_uav = uav['speed'] * uav['flight_time'] * uav['swath_width']
			total_max_coverage_capability += max_area_per_uav

		print(f"区域总面积需求: {total_area_needed:.2f} m²")
		print(f"无人机队理论最大总覆盖能力: {total_max_coverage_capability:.2f} m²")

		if total_max_coverage_capability < total_area_needed:
			print("【警告】无法覆盖该区域：机队总覆盖能力小于区域面积需求。")
			return False
		else:
			print("【成功】预检查通过，机队理论上有能力覆盖该区域。")
			return True

	def decompose_area_and_assign(self, n_points_per_sq_km=5):
		print(f"\n--- 步骤 1: 使用K-Means和泰森多边形进行无缝区域分解 ---")
		area_sq_km = self.total_area_shape_utm.area / 1_000_000
		n_points = max(self.num_uavs * 50, int(area_sq_km * n_points_per_sq_km))
		min_x, min_y, max_x, max_y = self.total_area_shape_utm.bounds
		points_inside = []
		while len(points_inside) < n_points:
			rand_points = np.random.rand(n_points * 2, 2)
			rand_points[:, 0] = rand_points[:, 0] * (max_x - min_x) + min_x
			rand_points[:, 1] = rand_points[:, 1] * (max_y - min_y) + min_y
			for p in rand_points:
				if len(points_inside) >= n_points: break
				if self.total_area_shape_utm.contains(Point(p)):
					points_inside.append(p)
		points_arr = np.array(points_inside)
		kmeans = KMeans(n_clusters=self.num_uavs, random_state=42, n_init=10).fit(points_arr)
		centers = MultiPoint(kmeans.cluster_centers_)
		voronoi_cells = voronoi_diagram(centers, envelope=self.total_area_shape_utm)
		print(f"已生成 {len(voronoi_cells.geoms)} 个泰森多边形单元格。")
		self.results = []
		for i, center_point in enumerate(centers.geoms):
			uav = self.uavs[i]
			assigned_cell = None
			for cell in voronoi_cells.geoms:
				if cell.contains(center_point):
					assigned_cell = cell
					break
			if assigned_cell:
				sub_area_utm = self.total_area_shape_utm.intersection(assigned_cell)
			else:
				sub_area_utm = Polygon()
			self.results.append({"uav_id": uav['id'], "uav_params": uav, "sub_area_utm": sub_area_utm})
		print("无缝区域分解与分配完成。")

	def plan_paths_for_all(self):
		print("\n--- 步骤 2: 在UTM坐标系下为每个子区域规划路径 ---")
		for result in self.results:
			uav = result['uav_params']
			sub_area_utm = result['sub_area_utm']
			if sub_area_utm.is_empty:
				print(f"  - 无人机 {uav['id']} 分配区域为空，跳过。")
				result.update({'path_utm': None, 'path_length': 0, 'flight_duration_needed': 0, 'is_feasible': True})
				continue
			print(f"正在为无人机 {uav['id']} 规划路径...")
			path_utm, path_length = generate_s_path_in_polygon(sub_area_utm, uav['swath_width'])
			result['path_utm'] = path_utm
			result['path_length'] = path_length or 0
			if path_length and uav['speed'] > 0:
				duration = path_length / uav['speed']
				result['flight_duration_needed'] = duration
				result['is_feasible'] = duration <= uav['flight_time']
			else:
				result['flight_duration_needed'] = 0
				result['is_feasible'] = True

	def calculate_coverage(self):
		print("\n--- 步骤 3: 在UTM坐标系下计算最终覆盖率 ---")
		all_coverage_polygons_utm = []
		for result in self.results:
			if result.get('path_utm') and not result['path_utm'].is_empty:
				uav = result['uav_params']
				coverage_poly_utm = result['path_utm'].buffer(uav['swath_width'] / 2, cap_style=2)
				all_coverage_polygons_utm.append(coverage_poly_utm)
		if not all_coverage_polygons_utm:
			self.coverage_percentage = 0.0
			return
		total_coverage_union_utm = unary_union(all_coverage_polygons_utm)
		effective_coverage_utm = self.total_area_shape_utm.intersection(total_coverage_union_utm)
		self.coverage_percentage = (effective_coverage_utm.area / self.total_area_shape_utm.area) * 100
		print(f"原始区域总面积: {self.total_area_shape_utm.area:.2f} m²")
		print(f"有效覆盖总面积: {effective_coverage_utm.area:.2f} m²")
		print(f"最终覆盖率: {self.coverage_percentage:.2f}%")

	def visualize_plan(self, output_file="coverage_map_wuhan.html"):
		print(f"\n--- 步骤 4: 使用Folium可视化结果 ---")
		center_latlon = self.area_gdf_latlon.unary_union.centroid.coords[0][::-1]
		m = folium.Map(location=center_latlon, zoom_start=14, tiles="CartoDB positron")
		folium.GeoJson(
			self.area_gdf_latlon,
			style_function=lambda x: {'color': 'black', 'weight': 2, 'fillOpacity': 0.1, 'fillColor': 'gray'},
			name='原始观测区域', tooltip='原始观测区域'
		).add_to(m)
		colors = plt.cm.get_cmap('viridis', self.num_uavs)
		for i, result in enumerate(self.results):
			uav_id = result['uav_id']
			color_hex = plt.cm.colors.to_hex(colors(i))
			feature_group = folium.FeatureGroup(name=f"无人机 {uav_id} (UAV {uav_id})", show=True)
			sub_area_utm = result.get('sub_area_utm')
			if sub_area_utm and not sub_area_utm.is_empty:
				sub_area_latlon = gpd.GeoSeries([sub_area_utm], crs=self.utm_crs).to_crs(self.original_crs)
				folium.GeoJson(sub_area_latlon,
				               style_function=lambda x, c=color_hex: {'color': c, 'weight': 1.5, 'fillColor': c,
				                                                      'fillOpacity': 0.25},
				               tooltip=f'无人机 {uav_id} 分配区域').add_to(feature_group)
			path_utm = result.get('path_utm')
			if path_utm and not path_utm.is_empty:
				uav = result['uav_params']
				coverage_poly_utm = path_utm.buffer(uav['swath_width'] / 2, cap_style=2)
				path_latlon = gpd.GeoSeries([path_utm], crs=self.utm_crs).to_crs(self.original_crs)
				coverage_latlon = gpd.GeoSeries([coverage_poly_utm], crs=self.utm_crs).to_crs(self.original_crs)
				folium.GeoJson(coverage_latlon,
				               style_function=lambda x, c=color_hex: {'color': 'transparent', 'fillColor': c,
				                                                      'fillOpacity': 0.4},
				               tooltip=f'无人机 {uav_id} 覆盖范围').add_to(feature_group)
				folium.GeoJson(path_latlon, style_function=lambda x, c=color_hex: {'color': c, 'weight': 2.5},
				               tooltip=f"无人机 {uav_id} 路径").add_to(feature_group)
			feature_group.add_to(m)
		folium.LayerControl(collapsed=False).add_to(m)
		m.save(output_file)
		print(f"可视化地图已保存至: {output_file}")

	# ====================================================================
	# === 【新增功能 2】返回并保存JSON格式的结果 ===
	# ====================================================================
	def get_results_as_json(self):
		"""将最终的规划结果整理成一个字典，以便转换为JSON"""
		summary_data = {
			"total_area_sqm": self.total_area_shape_utm.area,
			"final_coverage_percentage": self.coverage_percentage,
			"uav_results": []
		}
		for res in self.results:
			uav_p = res['uav_params']
			sub_area_utm = res.get('sub_area_utm')
			# 将子区域的几何形状转换为GeoJSON格式
			sub_area_latlon_geom = None
			if sub_area_utm and not sub_area_utm.is_empty:
				sub_area_latlon = gpd.GeoSeries([sub_area_utm], crs=self.utm_crs).to_crs(self.original_crs)
				# 使用 `__geo_interface__` 是一种标准的转换方式
				sub_area_latlon_geom = sub_area_latlon.iloc[0].__geo_interface__

			uav_result = {
				"uav_id": res['uav_id'],
				"is_feasible": res.get('is_feasible', False),
				"assigned_area_sqm": sub_area_utm.area if sub_area_utm else 0,
				"path_length_m": res.get('path_length', 0),
				"estimated_flight_time_s": res.get('flight_duration_needed', 0),
				"max_flight_time_s": uav_p['flight_time'],
				"assigned_area_geojson": sub_area_latlon_geom
			}
			summary_data["uav_results"].append(uav_result)
		return summary_data

	def print_summary_report(self):
		"""将总结报告打印到控制台"""
		print("\n\n" + "=" * 50)
		print(" " * 15 + "协同观测规划总结报告")
		print("=" * 50)
		for res in self.results:
			uav = res['uav_params']
			status = "✅ 可行" if res.get('is_feasible', False) else "❌ 超出续航"
			print(f"\n[无人机 ID: {res['uav_id']}]")
			print(f"  - 分配区域面积: {res.get('sub_area_utm', Polygon()).area:.2f} m²")
			print(f"  - 规划路径长度: {res.get('path_length', 0):.2f} m")
			print(f"  - 预计飞行时间: {res.get('flight_duration_needed', 0):.2f} s / {uav['flight_time']} s")
			print(f"  - 任务可行性: {status}")
		print("\n" + "-" * 50)
		print(f"最终总覆盖率: {self.coverage_percentage:.2f}%")
		print("=" * 50)


# ==============================================================================
# 3. 主执行流程 (Main Execution Flow)
# ==============================================================================

if __name__ == '__main__':
	GEOJSON_FILE = "wuhan_east_lake.geojson"
	create_wuhan_geojson(GEOJSON_FILE)

	UAV_FLEET = [
		{'id': 1, 'speed': 25.0, 'flight_time': 3000, 'swath_width': 30},
		{'id': 2, 'speed': 25.0, 'flight_time': 3000, 'swath_width': 40},
		{'id': 3, 'speed': 20.0, 'flight_time': 2400, 'swath_width': 25},
		{'id': 4, 'speed': 20.0, 'flight_time': 2400, 'swath_width': 30},
		{'id': 5, 'speed': 25.0, 'flight_time': 2400, 'swath_width': 25},
		{'id': 6, 'speed': 20.0, 'flight_time': 2400, 'swath_width': 20},
		{'id': 7, 'speed': 25.0, 'flight_time': 2000, 'swath_width': 15},
		{'id': 8, 'speed': 25.0, 'flight_time': 2000, 'swath_width': 25},
	]

	# 初始化规划器
	planner = MultiUAVPlanner(geojson_path=GEOJSON_FILE, uavs_params=UAV_FLEET)

	# --- 执行可行性预检查 ---
	if not planner.pre_check_feasibility():
		# 如果预检查失败，则终止程序
		sys.exit("规划终止，请调整无人机参数或更换机队。")

	# --- 如果检查通过，则执行完整规划流程 ---
	planner.decompose_area_and_assign()
	planner.plan_paths_for_all()
	planner.calculate_coverage()
	planner.visualize_plan()

	# --- 输出结果 ---
	# 1. 保存JSON结果
	results_data = planner.get_results_as_json()
	json_output_file = "planning_results.json"
	with open(json_output_file, 'w', encoding='utf-8') as f:
		json.dump(results_data, f, ensure_ascii=False, indent=4)
	print(f"JSON格式的结果已保存至: {json_output_file}")

	# 2. 打印控制台报告
	planner.print_summary_report()