#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武汉市卫星+无人机协同覆盖规划器 (v3.2 - 集成通用规划器)
功能：调用通用卫星规划器进行分析 + 调用高层场景函数进行补全规划
"""

import json
import sys
import os
import traceback

# --- 导入所有工具函数 ---
from satelliteTool.find_Satellite import get_valid_satellite_tle_as_dict
from DeployTool.UAV_GS_planner import run_planning_scenario
import geopandas as gpd
from shapely.geometry import shape, mapping, Point
from shapely.ops import unary_union

# ==============================================================================
# ** 导入新的通用卫星规划器函数 **
# ==============================================================================
# !! 请确保将你在Canvas中选择的通用规划器代码保存为 satellite_planner.py 文件 !!
from DeployTool.satellite_observation_planner import plan_satellite_observation


def load_tle_data(tle_file_path="satelliteTool/tle_data.json"):
	"""加载TLE数据"""
	with open(tle_file_path, 'r', encoding='utf-8') as f:
		return json.load(f)


def load_wuhan_boundary(geojson_path="geojson/Wuhan.geojson"):
	"""加载武汉市边界"""
	with open(geojson_path, 'r', encoding="utf-8") as f:
		return json.load(f)


def get_utm_crs(gdf_latlon):
	"""为给定的GeoDataFrame计算合适的UTM坐标参考系。"""
	try:
		centroid = gdf_latlon.unary_union.centroid
		lon, lat = centroid.x, centroid.y
		utm_band = str(int((lon + 180) // 6 + 1))
		epsg_code = '326' + utm_band.zfill(2) if lat >= 0 else '327' + utm_band.zfill(2)
		return f"EPSG:{epsg_code}"
	except Exception:
		return "EPSG:32649"


def create_comprehensive_visualization(wuhan_boundary, uncovered_area,
                                       completion_results, planning_mode, satellite_plan_data=None,
                                       output_file="comprehensive_coverage_map.html"):
	"""创建信息丰富的综合可视化地图"""
	print("\n=== 正在创建最终的综合可视化地图... ===")
	try:
		import folium

		center_lat, center_lon = 30.547, 114.405
		m = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles="CartoDB positron")

		folium.GeoJson(wuhan_boundary, name='总任务区域（武汉市）',
		               style_function=lambda x: {'color': 'black', 'weight': 3, 'fillOpacity': 0.05,
		                                         'fillColor': 'black'}, tooltip='总任务区域').add_to(m)

		# 可视化卫星方案 (无论是'optimal'还是'best_effort')
		if satellite_plan_data:
			plan_name = "卫星最优方案" if satellite_plan_data['is_optimal'] else "卫星尽力而为方案"
			coverage_ratio = satellite_plan_data['coverage_ratio']
			footprints = satellite_plan_data['intersection_footprints']

			folium.GeoJson({"type": "FeatureCollection", "features": footprints},
			               name=plan_name,
			               style_function=lambda x: {'color': 'blue', 'weight': 0, 'fillColor': 'blue',
			                                         'fillOpacity': 0.4},
			               tooltip=f'{plan_name} (覆盖率: {coverage_ratio:.2%})').add_to(m)

		if uncovered_area and uncovered_area.get('features'):
			folium.GeoJson(uncovered_area, name='卫星未覆盖区域 (无人机任务区)',
			               style_function=lambda x: {'color': 'orange', 'weight': 2, 'dashArray': '5, 5',
			                                         'fillColor': 'orange', 'fillOpacity': 0.1},
			               tooltip='需要补全的区域').add_to(m)
		if completion_results:
			gs_contribution = completion_results.get("ground_station_contribution", {})
			if gs_contribution and gs_contribution.get("stations_details"):
				gs_group = folium.FeatureGroup(name="地面站贡献", show=True).add_to(m)
				for gs_detail in gs_contribution["stations_details"]:
					lon, lat = gs_detail['coords_latlon']
					radius_m = gs_detail['radius_m']
					gs_point = Point(lon, lat)
					gs_gdf = gpd.GeoDataFrame(geometry=[gs_point], crs="EPSG:4326")
					utm_crs = get_utm_crs(gs_gdf)
					gs_coverage_latlon = gs_gdf.to_crs(utm_crs).buffer(radius_m).to_crs("EPSG:4326")
					folium.GeoJson(gs_coverage_latlon,
					               style_function=lambda x: {'color': 'red', 'weight': 2, 'fillColor': 'red',
					                                         'fillOpacity': 0.3},
					               tooltip=f"地面站 {gs_detail['id']} (半径: {radius_m} m)").add_to(gs_group)
					folium.Marker(location=[lat, lon], popup=f"地面站 {gs_detail['id']}",
					              icon=folium.Icon(color='red', icon='broadcast-tower', prefix='fa')).add_to(gs_group)
			uav_results = completion_results.get("uav_results", [])
			if uav_results:
				import matplotlib.cm as cm
				import matplotlib.colors as colors
				uav_count = len(uav_results)
				cmap = cm.get_cmap('viridis', uav_count if uav_count > 0 else 1)
				for i, uav_res in enumerate(uav_results):
					uid = uav_res.get('uav_id', i + 1)
					color = colors.to_hex(cmap(i))
					fg = folium.FeatureGroup(name=f"无人机 {uid}", show=True).add_to(m)
					if uav_res.get("assigned_area_geojson"):
						feature = {"type": "Feature", "geometry": uav_res["assigned_area_geojson"], "properties": {}}
						assigned_area_gdf = gpd.GeoDataFrame.from_features([feature], crs="EPSG:4326")
						folium.GeoJson(assigned_area_gdf,
						               style_function=lambda x, c=color: {'color': c, 'weight': 2, 'dashArray': '5, 5',
						                                                  'fillOpacity': 0.2, 'fillColor': c},
						               tooltip=f'无人机 {uid} 分配区域').add_to(fg)

		folium.LayerControl(collapsed=False, position='topleft').add_to(m)
		m.save(output_file)
		print(f"✅ 综合可视化地图已保存到: {output_file}")
		return output_file
	except Exception as e:
		print(f"❌ 生成综合可视化地图时出错: {e}")
		traceback.print_exc()
		return None


def main():
	"""主函数 (集成通用规划器版)"""
	print("� 武汉市卫星+无人机协同覆盖规划器 (v3.2 - 集成版)")
	print("=" * 60)

	# --- 步骤 1: 调用通用卫星规划器进行分析 ---
	# 使用 get_valid_satellite_tle_as_dict 按需筛选卫星
	tle_data = get_valid_satellite_tle_as_dict(satellite_db_path='data/satellite_data.db',
	                                           mission_theme='Land cover',
	                                           sensor_type='Optical Sensor')
	wuhan_boundary = load_wuhan_boundary()
	wuhan_geojson_path = "geojson/Wuhan.geojson"

	sat_plan_results = plan_satellite_observation(
		target_geojson_path=wuhan_geojson_path,
		tle_dict=tle_data,
		start_time="2025-08-01 00:00:00.000",
		end_time="2025-08-01 23:59:59.000",
		target_coverage=0.99,
		fov=11.0,
		interval_seconds=600,
		output_dir="satellite_planning_output"
	)

	# --- 步骤 2: 处理卫星规划结果，计算未覆盖区域 ---
	final_plan = (sat_plan_results['report']['optimal_plan'] or
	              sat_plan_results['report']['best_effort_plan'])

	if not final_plan:
		print("❌ 卫星规划失败或未找到任何相交卫星，无法进行无人机补全。")
		return

	total_coverage = final_plan['coverage']
	is_optimal = sat_plan_results['success']

	if is_optimal:
		print(f"\n🛰️  卫星最优方案已找到，覆盖率: {total_coverage:.2%}")
	else:
		print(f"\n🛰️  未找到满足目标的方案，采纳'尽力而为'的最佳方案，覆盖率: {total_coverage:.2%}")

	if total_coverage >= 0.99:
		print(f"✅ 卫星覆盖率已达到 {total_coverage:.2%}，无需无人机补全。")
		# (可视化并退出)
		with open(sat_plan_results['intersection_geojson_path'], 'r', encoding='utf-8') as f:
			covered_geojson = json.load(f)
		satellite_plan_data = {
			"is_optimal": is_optimal, "coverage_ratio": total_coverage,
			"intersection_footprints": covered_geojson['features']
		}
		create_comprehensive_visualization(
			wuhan_boundary=wuhan_boundary, uncovered_area=None, completion_results=None,
			planning_mode="仅卫星", satellite_plan_data=satellite_plan_data,
			output_file="final_coverage_map.html"
		)
		return

	print(f"⚠️  卫星覆盖率 {total_coverage:.2%} < 99%，开始计算无人机补全区域。")

	wuhan_shape = unary_union([shape(f['geometry']) for f in wuhan_boundary['features'] if f.get('geometry')])
	with open(sat_plan_results['intersection_geojson_path'], 'r', encoding='utf-8') as f:
		covered_geojson = json.load(f)
	covered_shape = unary_union([shape(f['geometry']) for f in covered_geojson['features'] if f.get('geometry')])
	uncovered_geom = wuhan_shape.difference(covered_shape)

	uncovered_area = {
		"type": "FeatureCollection",
		"features": [{"type": "Feature", "geometry": mapping(uncovered_geom), "properties": {}}]
	}

	if uncovered_geom.is_empty:
		print("✅ 计算后发现未覆盖区域为空，无需进行补全规划。")
		return

	# --- 步骤 3: 调用无人机补全规划 ---
	print("\n" + "=" * 20 + " 步骤3: 调用无人机场景函数进行补全规划 " + "=" * 20)
	TEMP_FILE_PATH = "temp_uncovered_for_scenario.geojson"
	OUTPUT_DIR = "completion_results"
	completion_results = None
	try:
		with open(TEMP_FILE_PATH, 'w', encoding='utf-8') as f:
			json.dump(uncovered_area, f)
		completion_results = run_planning_scenario(
			geojson_path=TEMP_FILE_PATH,
			output_dir=OUTPUT_DIR,
			create_map=True,
			verbose=True,
			UAV_db_path="data/UAV_data.db",
			stations_db_path="data/Stations_data.db"
		)
	finally:
		if os.path.exists(TEMP_FILE_PATH):
			os.remove(TEMP_FILE_PATH)
			print(f"\n临时文件 '{TEMP_FILE_PATH}' 已删除。")

	# --- 步骤 4: 处理结果并生成最终的综合地图 ---
	if completion_results:
		print(f"\n🎉 补全规划成功！详细结果保存在 '{OUTPUT_DIR}' 文件夹中。")
		planning_mode = "空地协同" if completion_results.get("ground_station_contribution", {}).get("station_count",
		                                                                                        0) > 0 else "纯无人机"

		satellite_plan_data = {
			"is_optimal": is_optimal, "coverage_ratio": total_coverage,
			"intersection_footprints": covered_geojson['features']
		}

		create_comprehensive_visualization(
			wuhan_boundary=wuhan_boundary,
			uncovered_area=uncovered_area,
			completion_results=completion_results,
			planning_mode=planning_mode,
			satellite_plan_data=satellite_plan_data,
			output_file="final_coverage_map.html"
		)
	else:
		print("\n❌ 补全规划失败。")


if __name__ == "__main__":
	main()