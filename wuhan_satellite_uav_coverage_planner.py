#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武汉市卫星+无人机协同覆盖规划器
功能：卫星覆盖分析 + 无人机/地面站补全规划
"""

import json
import sys
import os
import geopandas as gpd

# 添加路径
sys.path.append('satelliteTool')
sys.path.append('GeoPandasTool')
sys.path.append('ConfigureTool')

from satelliteTool.get_observation_lace import get_coverage_lace
from satelliteTool.get_observation_overlap import get_observation_overlap
from GeoPandasTool.difference import difference
from GeoPandasTool.is_valid import is_valid
from GeoPandasTool.is_valid_reason import is_valid_reason
from GeoPandasTool.contains import contains
from ConfigureTool.UAV_GS_planner import CollaborativePlanner
from ConfigureTool.UAV_Planner import MultiUAVPlanner


def load_tle_data(tle_file_path="satelliteTool/tle_data.json"):
	"""加载TLE数据"""
	with open(tle_file_path, 'r') as f:
		return json.load(f)


def load_wuhan_boundary(geojson_path="geojson/Wuhan.geojson"):
	"""加载武汉市边界"""
	try:
		with open(geojson_path, 'r') as f:
			return json.load(f)
	except:
		# 简化边界
		return {
			"type": "FeatureCollection",
			"features": [{
				"type": "Feature",
				"geometry": {
					"type": "Polygon",
					"coordinates": [[[114.0, 30.0], [114.8, 30.0], [114.8, 30.8], [114.0, 30.8], [114.0, 30.0]]]
				}
			}]
		}


# ==============================================================================
# 关键修复：添加缺失的 get_utm_crs 辅助函数
# ==============================================================================
def get_utm_crs(gdf_latlon):
	"""
	为给定的GeoDataFrame计算合适的UTM坐标参考系。
	"""
	try:
		# 计算几何中心的经纬度
		centroid = gdf_latlon.unary_union.centroid
		lon, lat = centroid.x, centroid.y

		# 根据经度计算UTM带号
		utm_band = str(int((lon + 180) // 6 + 1))

		# 根据纬度确定是北半球还是南半球
		if lat >= 0:
			epsg_code = '326' + utm_band.zfill(2)
		else:
			epsg_code = '327' + utm_band.zfill(2)
		return f"EPSG:{epsg_code}"
	except Exception:
		# 如果计算失败，返回一个适用于武汉地区的默认UTM带
		return "EPSG:32649"


def find_optimal_ground_station_location(uncovered_area, wuhan_boundary):
	"""在未覆盖区域内找到最优地面站位置"""
	print("=== 寻找最优地面站位置 ===")

	try:
		# 检查未覆盖区域是否存在有效的几何图形
		if not uncovered_area.get('features') or not uncovered_area['features'][0].get('geometry'):
			print("⚠️  没有未覆盖区域，无法放置地面站")
			return None

		# 使用geopandas从geojson特征创建GeoDataFrame，CRS设为WGS84
		gdf = gpd.GeoDataFrame.from_features(uncovered_area['features'], crs="EPSG:4326")

		# 计算所有几何图形合并后的质心
		centroid = gdf.unary_union.centroid

		ground_station = {
			'coords_latlon': [centroid.x, centroid.y],
			'observation_radius_m': 4000
		}

		print(f"✅ 地面站位置: [{centroid.x:.6f}, {centroid.y:.6f}]")
		print(f"   观测半径: {ground_station['observation_radius_m']} 米")
		return ground_station

	except Exception as e:
		print(f"⚠️  计算地面站位置时出错: {e}")
		return None


def check_ground_station_coverage(ground_station, uncovered_area):
	"""检查地面站是否位于非观测区域内"""
	print("=== 检查地面站覆盖情况 ===")

	try:
		ground_station_geojson = {
			"type": "FeatureCollection",
			"features": [
				{"type": "Feature", "geometry": {"type": "Point", "coordinates": ground_station['coords_latlon']}}]
		}

		uncovered_str = json.dumps(uncovered_area)
		gs_str = json.dumps(ground_station_geojson)

		contains_results = contains(uncovered_str, gs_str)
		is_in_uncovered = any(contains_results) if contains_results else False

		if is_in_uncovered:
			print("✅ 地面站位于非卫星覆盖区域内，可以使用空地协同规划")
		else:
			print("⚠️  地面站不在非卫星覆盖区域内，将使用纯无人机规划")

		return is_in_uncovered

	except Exception as e:
		print(f"⚠️  检查地面站覆盖情况时出错: {e}")
		print("默认使用纯无人机规划")
		return False


def analyze_satellite_coverage(tle_data, wuhan_boundary):
	"""分析卫星覆盖率"""
	print("=== 步骤1: 分析卫星覆盖率 ===")

	try:
		coverage_dict = get_coverage_lace(
			tle_dict=tle_data,
			start_time_str="2025-08-01 00:00:00.000",
			end_time_str="2025-08-01 23:59:59.000",
			fov=10.0,
			interval_seconds=600
		)

		# 统计总特征数量
		total_features = sum(len(geojson['features']) for geojson in coverage_dict.values())
		print(f"成功生成卫星覆盖轨迹，涉及 {len(coverage_dict)} 颗卫星，总特征数量: {total_features}")

		overlap_results = get_observation_overlap(
			tle_dict=tle_data,
			start_time_str="2025-08-01 00:00:00.000",
			end_time_str="2025-08-01 23:59:59.000",
			target_geojson=wuhan_boundary,
			fov=10.0,
			interval_seconds=600
		)

		total_coverage = sum(data['coverage_ratio'] for data in overlap_results.values()) if overlap_results else 0
		print(f"卫星总覆盖率: {total_coverage:.2%}")

		return coverage_dict, overlap_results, total_coverage

	except Exception as e:
		print(f"⚠️  卫星覆盖分析时出错: {e}")
		empty_coverage = {}
		return empty_coverage, {}, 0.0


def get_uncovered_area(wuhan_boundary, coverage_dict):
	"""获取卫星无法覆盖的区域"""
	print("=== 步骤2: 计算未覆盖区域 ===")

	if not coverage_dict:
		print("卫星覆盖数据为空，返回整个区域作为未覆盖区。")
		return wuhan_boundary

	# 合并所有卫星的覆盖特征
	all_features = []
	for satellite_name, satellite_geojson in coverage_dict.items():
		if satellite_geojson.get('features'):
			all_features.extend(satellite_geojson['features'])

	if not all_features:
		print("⚠️  没有有效的卫星覆盖数据，返回原始边界作为未覆盖区域")
		return wuhan_boundary

	# 创建合并的覆盖GeoJSON
	merged_coverage = {"type": "FeatureCollection", "features": all_features}
	coverage_str = json.dumps(merged_coverage)

	# 检查几何有效性
	validity_results = is_valid(coverage_str)
	valid_features = [feature for i, feature in enumerate(all_features) if validity_results[i]]

	if not valid_features:
		print("⚠️  没有有效的卫星覆盖数据，返回原始边界作为未覆盖区域")
		return wuhan_boundary

	cleaned_coverage = {"type": "FeatureCollection", "features": valid_features}
	print(f"有效覆盖特征数量: {len(valid_features)}")

	try:
		coverage_str = json.dumps(cleaned_coverage)
		wuhan_str = json.dumps(wuhan_boundary)

		uncovered_geojson_str = difference(wuhan_str, coverage_str)
		return json.loads(uncovered_geojson_str)

	except Exception as e:
		print(f"⚠️  计算未覆盖区域时出错: {e}")
		return wuhan_boundary


def plan_uav_coverage(uncovered_area, ground_station=None):
	"""规划无人机覆盖，并返回包含完整几何信息的丰富结果"""
	print("=== 步骤3: 规划无人机/空地协同覆盖 ===")

	temp_file = "temp_uncovered_area.geojson"
	with open(temp_file, 'w') as f:
		json.dump(uncovered_area, f)

	uav_fleet = [
		{'id': 1, 'speed': 2500.0, 'flight_time': 30000, 'swath_width': 1000},
		{'id': 2, 'speed': 2500.0, 'flight_time': 30000, 'swath_width': 1200},
		{'id': 3, 'speed': 2000.0, 'flight_time': 24000, 'swath_width': 1500},
		{'id': 4, 'speed': 2500.0, 'flight_time': 30000, 'swath_width': 1000},
		{'id': 5, 'speed': 2500.0, 'flight_time': 30000, 'swath_width': 1500},
		{'id': 6, 'speed': 2000.0, 'flight_time': 24000, 'swath_width': 1000},
	]

	planner = None
	map_filename = ""
	if ground_station:
		print("使用空地协同规划器 (UAV_GS_planner)")
		planner = CollaborativePlanner(
			geojson_path=temp_file,
			uavs_params=uav_fleet,
			ground_station_params=ground_station
		)
		map_filename = "collaborative_coverage_map.html"
	else:
		print("使用多无人机规划器 (UAV_Planner)")
		planner = MultiUAVPlanner(
			geojson_path=temp_file,
			uavs_params=uav_fleet
		)
		map_filename = "uav_coverage_map.html"

	if planner.pre_check_feasibility():
		planner.decompose_area_and_assign()
		planner.plan_paths_for_all()
		planner.calculate_coverage()
		planner.visualize_plan(map_filename)

		rich_results = {
			"total_area_sqm": planner.total_area_shape_utm.area,
			"final_coverage_percentage": planner.coverage_percentage,
			"uav_results": []
		}

		if hasattr(planner, 'ground_station') and planner.ground_station:
			rich_results["ground_station_contribution"] = {
				"coords_latlon": planner.ground_station['coords_latlon'],
				"observation_radius_m": planner.ground_station['observation_radius_m']
			}

		for res in planner.results:
			sub_area_utm = res.get('sub_area_utm')
			path_utm = res.get('path_utm')

			sub_area_geojson, path_geojson, coverage_geojson = None, None, None

			if sub_area_utm and not sub_area_utm.is_empty:
				sub_area_geojson = gpd.GeoSeries([sub_area_utm], crs=planner.utm_crs).to_crs("EPSG:4326").iloc[
					0].__geo_interface__

			if path_utm and not path_utm.is_empty:
				path_geojson = gpd.GeoSeries([path_utm], crs=planner.utm_crs).to_crs("EPSG:4326").iloc[
					0].__geo_interface__
				coverage_poly_utm = path_utm.buffer(res['uav_params']['swath_width'] / 2, cap_style=2)
				coverage_geojson = gpd.GeoSeries([coverage_poly_utm], crs=planner.utm_crs).to_crs("EPSG:4326").iloc[
					0].__geo_interface__

			uav_res = {
				"uav_id": res['uav_id'], "is_feasible": res.get('is_feasible', False),
				"assigned_area_sqm": sub_area_utm.area if sub_area_utm else 0,
				"path_length_m": res.get('path_length', 0),
				"estimated_flight_time_s": res.get('flight_duration_needed', 0),
				"max_flight_time_s": res['uav_params']['flight_time'],
				"assigned_area_geojson": sub_area_geojson, "path_geojson": path_geojson,
				"coverage_geojson": coverage_geojson
			}
			rich_results["uav_results"].append(uav_res)

		planner.print_summary_report()
		os.remove(temp_file)
		return rich_results, map_filename, ground_station
	else:
		print("无人机规划可行性检查失败")
		os.remove(temp_file)
		return None, None, None


def create_comprehensive_visualization(wuhan_boundary, satellite_coverage_dict, uncovered_area,
                                       uav_results, ground_station_info, total_coverage,
                                       planning_mode, overlap_results=None, output_file="comprehensive_coverage_map.html"):
	"""创建信息丰富的综合可视化地图

	Args:
		wuhan_boundary: 武汉市边界GeoJSON
		satellite_coverage_dict: 卫星覆盖数据字典
		uncovered_area: 未覆盖区域GeoJSON
		uav_results: 无人机规划结果
		ground_station_info: 地面站信息
		total_coverage: 总覆盖率
		planning_mode: 规划模式
		overlap_results: 卫星与研究区域的相交结果（包含相交足迹）
		output_file: 输出文件名
	"""
	print("=== 创建综合可视化地图 ===")

	try:
		import folium
		from shapely.geometry import Point

		center_lat, center_lon = 30.547, 114.405
		m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="CartoDB positron")

		# 1. 总任务区域
		folium.GeoJson(wuhan_boundary, name='总任务区域（武汉市）',
		               style_function=lambda x: {'color': 'black', 'weight': 3, 'fillOpacity': 0.05,
		                                         'fillColor': 'black'},
		               tooltip='总任务区域'
		               ).add_to(m)

		# 2. 卫星覆盖（只显示与研究区域相交的部分）
		if overlap_results:
			# 使用已经计算好的相交足迹数据
			for satellite_name, data in overlap_results.items():
				intersection_footprints = data['intersection_footprints']
				if intersection_footprints:
					intersection_geojson = {
						"type": "FeatureCollection",
						"features": intersection_footprints
					}
					folium.GeoJson(intersection_geojson, name=f'卫星覆盖-{satellite_name}',
					               style_function=lambda x: {'color': 'blue', 'weight': 0, 'fillColor': 'blue',
					                                         'fillOpacity': 0.4},
					               tooltip=f'{satellite_name} 相交覆盖区域 (覆盖率: {data["coverage_ratio"]:.2%})'
					               ).add_to(m)
		elif satellite_coverage_dict:
			# 如果没有相交数据，回退到显示所有足迹（但这不是推荐的做法）
			print("⚠️  没有相交足迹数据，显示所有卫星足迹")
			for satellite_name, satellite_geojson in satellite_coverage_dict.items():
				if satellite_geojson and satellite_geojson.get('features'):
					folium.GeoJson(satellite_geojson, name=f'卫星覆盖-{satellite_name}',
					               style_function=lambda x: {'color': 'blue', 'weight': 0, 'fillColor': 'blue',
					                                         'fillOpacity': 0.4},
					               tooltip=f'{satellite_name} 覆盖'
					               ).add_to(m)

		# 3. 卫星未覆盖（需要补全的区域）
		if uncovered_area and uncovered_area.get('features'):
			folium.GeoJson(uncovered_area, name='卫星未覆盖区域',
			               style_function=lambda x: {'color': 'orange', 'weight': 2, 'dashArray': '5, 5',
			                                         'fillColor': 'orange', 'fillOpacity': 0.1},
			               tooltip='需要无人机/地面站补全'
			               ).add_to(m)

		# 4. 地面站
		if ground_station_info:
			gs_group = folium.FeatureGroup(name="地面站", show=True).add_to(m)
			gs_point = Point(ground_station_info['coords_latlon'])
			gs_gdf = gpd.GeoDataFrame(geometry=[gs_point], crs="EPSG:4326")
			utm_crs = get_utm_crs(gs_gdf)
			gs_utm = gs_gdf.to_crs(utm_crs)
			gs_coverage_utm = gs_utm.buffer(ground_station_info['observation_radius_m'])
			gs_coverage_latlon = gs_coverage_utm.to_crs("EPSG:4326")

			folium.GeoJson(gs_coverage_latlon,
			               style_function=lambda x: {'color': 'red', 'weight': 2, 'fillColor': 'red',
			                                         'fillOpacity': 0.3},
			               tooltip=f"地面站半径: {ground_station_info['observation_radius_m']} m"
			               ).add_to(gs_group)

			folium.Marker(
				location=[gs_point.y, gs_point.x], popup="地面观测站",
				icon=folium.Icon(color='red', icon='broadcast-tower', prefix='fa')
			).add_to(gs_group)

		# 5. 无人机
		if uav_results and 'uav_results' in uav_results:
			import matplotlib.cm as cm
			import matplotlib.colors as colors

			uav_count = len(uav_results['uav_results'])
			color_map = cm.get_cmap('viridis', uav_count)

			for i, uav_res in enumerate(uav_results['uav_results']):
				uav_id = uav_res.get('uav_id', i + 1)
				color_hex = colors.to_hex(color_map(i))
				uav_group = folium.FeatureGroup(name=f"无人机 {uav_id}", show=True).add_to(m)

				if uav_res.get("assigned_area_geojson"):
					folium.GeoJson(uav_res["assigned_area_geojson"],
					               style_function=lambda x, c=color_hex: {'color': c, 'weight': 2, 'dashArray': '5, 5',
					                                                      'fillOpacity': 0.0},
					               tooltip=f'无人机 {uav_id} 分配区域'
					               ).add_to(uav_group)

				if uav_res.get("coverage_geojson"):
					folium.GeoJson(uav_res["coverage_geojson"],
					               style_function=lambda x, c=color_hex: {'color': 'transparent', 'fillColor': c,
					                                                      'fillOpacity': 0.4},
					               tooltip=f'无人机 {uav_id} 覆盖范围'
					               ).add_to(uav_group)

				if uav_res.get("path_geojson"):
					folium.GeoJson(uav_res["path_geojson"],
					               style_function=lambda x, c=color_hex: {'color': c, 'weight': 2.5},
					               tooltip=f'无人机 {uav_id} 飞行路径'
					               ).add_to(uav_group)

		folium.LayerControl(collapsed=False, position='topleft').add_to(m)
		m.save(output_file)
		print(f"✅ 综合可视化地图已保存到: {output_file}")
		return output_file

	except ImportError as e:
		print(f"❌ 缺少必要的库: {e}. 请安装: pip install folium geopandas matplotlib shapely")
		return None
	except Exception as e:
		print(f"❌ 生成综合可视化地图时出错: {e}")
		import traceback
		traceback.print_exc()
		return None


def main():
	"""主函数"""
	print("🚀 武汉市卫星+无人机协同覆盖规划器")
	print("=" * 60)

	tle_data = load_tle_data()
	wuhan_boundary = load_wuhan_boundary()

	coverage_dict, overlap_results, total_coverage = analyze_satellite_coverage(tle_data, wuhan_boundary)

	if total_coverage >= 0.9:
		print(f"✅ 卫星覆盖率已达到 {total_coverage:.2%}，无需补全")
		create_comprehensive_visualization(
			wuhan_boundary, coverage_dict, {"type": "FeatureCollection", "features": []}, None, None,
			total_coverage, "仅卫星", overlap_results, "comprehensive_coverage_map.html"
		)
		return

	print(f"⚠️  卫星覆盖率 {total_coverage:.2%} < 90%，需要补全")
	uncovered_area = get_uncovered_area(wuhan_boundary, coverage_dict)

	ground_station = find_optimal_ground_station_location(uncovered_area, wuhan_boundary)

	use_collaborative = False
	if ground_station:
		use_collaborative = check_ground_station_coverage(ground_station, uncovered_area)

	if use_collaborative:
		print("🎯 选择空地协同规划模式")
		uav_results, map_file, ground_station_info = plan_uav_coverage(uncovered_area, ground_station)
	else:
		print("🎯 选择纯无人机规划模式")
		uav_results, map_file, ground_station_info = plan_uav_coverage(uncovered_area, None)

	if uav_results:
		print(f"\n🎉 补全规划完成！规划器生成地图: {map_file}")
		comprehensive_map = create_comprehensive_visualization(
			wuhan_boundary=wuhan_boundary,
			satellite_coverage_dict=coverage_dict,
			uncovered_area=uncovered_area,
			uav_results=uav_results,
			ground_station_info=ground_station_info,
			total_coverage=total_coverage,
			planning_mode="空地协同" if use_collaborative else "纯无人机",
			overlap_results=overlap_results,
		)

		if comprehensive_map:
			print(f"综合可视化地图: {comprehensive_map}")

		with open("complete_coverage_planning.json", 'w', encoding='utf-8') as f:
			json.dump(uav_results, f, ensure_ascii=False, indent=4)
		print("无人机和地面站规划结果已保存到: complete_coverage_planning.json")
	else:
		print("❌ 无人机补全规划失败")


if __name__ == "__main__":
	main()