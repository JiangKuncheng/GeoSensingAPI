#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用卫星观测规划器
功能: 根据指定的观测区域、卫星数据和时间范围，规划最优的卫星覆盖方案。
"""

import json
from datetime import datetime
from itertools import combinations
import os

# 导入必要的地理信息处理库
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, transform
from pyproj import Proj, Transformer
import folium

# 导入您已经写好的工具函数
# 确保这些工具函数所在的目录在Python的搜索路径中
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from satelliteTool.find_Satellite import get_valid_satellite_tle_as_dict

"""
通用卫星观测规划器 (v2 - 增加'尽力而为'的最佳方案返回)
功能: 根据指定的观测区域、卫星数据和时间范围，规划最优的卫星覆盖方案。
"""

import json
from datetime import datetime
from itertools import combinations
import os

from shapely.geometry import shape, mapping
from shapely.ops import unary_union, transform
from pyproj import Proj, Transformer
import folium

from satelliteTool.get_observation_lace import get_coverage_lace
from satelliteTool.get_observation_overlap import get_observation_overlap


def plan_satellite_observation(
		target_geojson_path,
		tle_dict,
		start_time,
		end_time,
		target_coverage=0.9,
		fov=20.0,
		interval_seconds=600,
		output_dir="planning_results"
):
	"""
	一个通用的卫星观测规划函数 (v2)。
	如果找不到满足目标的方案，会返回一个由所有相交卫星组成的'尽力而为'方案。
	"""
	# ... (步骤 0 到 3 的代码保持不变) ...
	print("=" * 60)
	print("🚀 通用卫星观测规划器开始运行 🚀")
	print("=" * 60)

	# --- 步骤 0: 准备工作 ---
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
		print(f"创建输出目录: {output_dir}")

	try:
		with open(target_geojson_path, 'r', encoding='utf-8') as f:
			target_geojson = json.load(f)
		area_name = os.path.basename(target_geojson_path).split('.')[0]
		print(f"✅ 成功加载观测区域: {area_name}")
	except Exception as e:
		print(f"❌ 加载观测区域GeoJSON失败: {e}")
		return {'success': False, 'message': 'Failed to load target GeoJSON.'}

	# --- 步骤 1: 获取所有卫星的覆盖足迹 (粗筛) ---
	print(f"\n[1/5] 正在获取卫星覆盖足迹 (时间: {start_time} 到 {end_time})...")
	try:
		coverage_dict = get_coverage_lace(
			tle_dict=tle_dict, start_time_str=start_time, end_time_str=end_time,
			fov=fov, interval_seconds=interval_seconds
		)
		total_features = sum(len(geojson.get('features', [])) for geojson in coverage_dict.values())
		print(f"✅ 成功生成 {total_features} 个足迹点，涉及 {len(coverage_dict)} 颗卫星")
	except Exception as e:
		print(f"❌ 获取卫星足迹失败: {e}")
		return {'success': False, 'message': f'Failed to get satellite footprints: {e}'}

	# --- 步骤 2: 筛选与观测区域相交的卫星 ---
	print("\n[2/5] 正在筛选与观测区域相交的卫星...")
	try:
		valid_target_geoms = []
		for feature in target_geojson.get('features', []):
			geom_json = feature.get('geometry')
			if geom_json:
				geom = shape(geom_json)
				if not geom.is_valid: geom = geom.buffer(0)
				if geom.is_valid and not geom.is_empty: valid_target_geoms.append(geom)
		if not valid_target_geoms: raise ValueError("目标GeoJSON中没有有效的几何对象")
		target_shape = unary_union(valid_target_geoms)

		intersecting_satellites = []
		for satellite_name, satellite_geojson in coverage_dict.items():
			valid_sat_geoms = []
			for feature in satellite_geojson.get('features', []):
				geom_json = feature.get('geometry')
				if geom_json:
					geom = shape(geom_json)
					if not geom.is_valid: geom = geom.buffer(0)
					if geom.is_valid and not geom.is_empty: valid_sat_geoms.append(geom)
			if not valid_sat_geoms: continue
			satellite_shape = unary_union(valid_sat_geoms)
			if target_shape.intersects(satellite_shape):
				intersecting_satellites.append(satellite_name)

		print(f"✅ 筛选完成，找到 {len(intersecting_satellites)} 颗相交卫星: {intersecting_satellites}")
		if not intersecting_satellites:
			print("❌ 未找到与目标区域相交的卫星，规划结束。")
			return {'success': False, 'message': 'No intersecting satellites found.',
			        'report': {'optimal_plan': None, 'best_effort_plan': None}}
	except Exception as e:
		print(f"❌ 在筛选卫星时发生错误: {e}")
		return {'success': False, 'message': f'Error during intersection check: {e}'}

	# --- 步骤 3: 精确计算每个相交卫星的覆盖率 ---
	print(f"\n[3/5] 正在精确计算卫星覆盖率...")
	filtered_tle_dict = {name: tle_dict[name] for name in intersecting_satellites}
	try:
		coverage_results = get_observation_overlap(
			tle_dict=filtered_tle_dict, start_time_str=start_time, end_time_str=end_time,
			target_geojson=target_geojson, fov=fov, interval_seconds=interval_seconds
		)
		print(f"✅ 覆盖率计算完成:")
		for satellite, data in coverage_results.items():
			print(f"   - {satellite}: 覆盖率 {data['coverage_ratio']:.2%}")
	except Exception as e:
		print(f"❌ 计算覆盖率失败: {e}")
		return {'success': False, 'message': f'Failed to calculate coverage overlap: {e}'}

	# --- 步骤 4: 寻找最优覆盖方案 ---
	print(f"\n[4/5] 正在寻找最优覆盖方案 (目标: {target_coverage:.0%})...")
	wgs84_proj = Proj('epsg:4326')
	equal_area_proj = Proj('+proj=moll')
	transformer = Transformer.from_proj(wgs84_proj, equal_area_proj, always_xy=True)
	target_area = transform(transformer.transform, target_shape).area

	optimal_plan = None
	best_effort_plan = None

	# 寻找满足目标的最优方案
	# ... (代码与之前版本相同) ...
	for satellite, data in coverage_results.items():
		if data['coverage_ratio'] >= target_coverage:
			optimal_plan = {'type': 'single', 'satellites': [satellite], 'coverage': data['coverage_ratio']}
			print(f"✅ 找到单个卫星解决方案: {satellite} (覆盖率: {data['coverage_ratio']:.2%})")
			break
	if not optimal_plan:
		sorted_satellites = sorted(coverage_results.keys(), key=lambda s: coverage_results[s]['coverage_ratio'],
		                           reverse=True)
		for combo_size in range(2, min(6, len(sorted_satellites) + 1)):
			for combo in combinations(sorted_satellites, combo_size):
				# ... (组合计算逻辑与之前版本相同) ...
				footprints = [shape(f['geometry']) for s in combo for f in
				              coverage_results[s]['intersection_footprints'] if f.get('geometry')]
				if not footprints: continue
				valid_footprints = [fp.buffer(0) if not fp.is_valid else fp for fp in footprints]
				valid_footprints = [fp for fp in valid_footprints if fp.is_valid and not fp.is_empty]
				if not valid_footprints: continue
				merged_footprints = unary_union(valid_footprints)
				projected_merged = transform(transformer.transform, merged_footprints)
				combo_coverage = projected_merged.area / target_area
				if combo_coverage >= target_coverage:
					optimal_plan = {'type': 'combination', 'satellites': list(combo), 'coverage': combo_coverage}
					print(f"✅ 找到最佳组合方案: {list(combo)} (覆盖率: {combo_coverage:.2%})")
					break
			if optimal_plan: break

	# --- START of MODIFICATION ---
	# 如果没有找到最优方案，则计算一个“尽力而为”的最佳方案
	if not optimal_plan:
		print("   未能找到满足目标的方案，正在计算'尽力而为'的最佳方案...")
		all_sats = list(coverage_results.keys())
		all_footprints = [shape(f['geometry']) for s in all_sats for f in coverage_results[s]['intersection_footprints']
		                  if f.get('geometry')]

		if all_footprints:
			valid_footprints = [fp.buffer(0) if not fp.is_valid else fp for fp in all_footprints]
			valid_footprints = [fp for fp in valid_footprints if fp.is_valid and not fp.is_empty]

			if valid_footprints:
				merged_all = unary_union(valid_footprints)
				projected_all = transform(transformer.transform, merged_all)
				best_effort_coverage = projected_all.area / target_area
				best_effort_plan = {
					'type': 'best_effort_combination',
					'satellites': all_sats,
					'coverage': best_effort_coverage
				}
				print(f"   ✅ '尽力而为'方案计算完成，合并所有卫星可达覆盖率: {best_effort_coverage:.2%}")

	# --- END of MODIFICATION ---

	# --- 步骤 5: 生成报告、地图和交集文件 ---
	print("\n[5/5] 正在生成最终结果...")
	plan_to_use = optimal_plan or best_effort_plan

	report = {
		'planning_period': {'start_time': start_time, 'end_time': end_time},
		'target_area_path': target_geojson_path,
		'target_coverage_goal': target_coverage,
		'intersecting_satellites_count': len(intersecting_satellites),
		'coverage_by_satellite': {k: v['coverage_ratio'] for k, v in coverage_results.items()},
		'optimal_plan': optimal_plan,  # 如果成功则有值，否则为None
		'best_effort_plan': best_effort_plan,  # 如果失败则有值，否则为None
		'generation_time': datetime.now().isoformat()
	}
	# ... (报告、地图、交集文件的生成逻辑与之前版本类似, 但使用 plan_to_use) ...
	report_path = os.path.join(output_dir, f"{area_name}_planning_report.json")
	with open(report_path, 'w', encoding='utf-8') as f:
		json.dump(report, f, ensure_ascii=False, indent=2)
	print(f"✅ 规划报告已保存到: {report_path}")

	m = folium.Map(location=[30.4, 114.4], zoom_start=7, tiles="CartoDB positron")
	folium.GeoJson(target_geojson, name=f'观测区域: {area_name}',
	               style_function=lambda x: {'color': 'black', 'weight': 3, 'fillOpacity': 0.1}).add_to(m)
	colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0']
	sorted_results = sorted(coverage_results.items(), key=lambda item: item[1]['coverage_ratio'], reverse=True)
	for i, (sat_name, data) in enumerate(sorted_results):
		if data.get('intersection_footprints'):
			layer_name = f"{sat_name} ({data['coverage_ratio']:.1%})"
			sat_layer = folium.FeatureGroup(name=layer_name, show=True)
			color = colors[i % len(colors)]
			folium.GeoJson(
				{"type": "FeatureCollection", "features": data['intersection_footprints']},
				style_function=lambda x, c=color: {'weight': 0, 'fillColor': c, 'fillOpacity': 0.35},
				tooltip=f"<b>{sat_name}</b><br>覆盖率: {data['coverage_ratio']:.2%}"
			).add_to(sat_layer)
			sat_layer.add_to(m)
	folium.LayerControl(collapsed=False).add_to(m)
	map_path = os.path.join(output_dir, f"{area_name}_coverage_map.html")
	m.save(map_path)
	print(f"✅ 可视化地图已保存到: {map_path}")

	intersection_geojson = {"type": "FeatureCollection", "features": []}
	if plan_to_use:
		sats_in_plan = plan_to_use['satellites']
		final_footprints_geom = [shape(f['geometry']) for s in sats_in_plan for f in
		                         coverage_results[s]['intersection_footprints'] if f.get('geometry')]
		if final_footprints_geom:
			valid_final_footprints = [fp.buffer(0) if not fp.is_valid else fp for fp in final_footprints_geom]
			valid_final_footprints = [fp for fp in valid_final_footprints if fp.is_valid and not fp.is_empty]
			if valid_final_footprints:
				final_union = unary_union(valid_final_footprints)
				final_intersection = final_union.intersection(target_shape)
				feature = {
					"type": "Feature",
					"geometry": mapping(final_intersection),
					"properties": {"satellites": sats_in_plan, "estimated_coverage": plan_to_use['coverage']}
				}
				intersection_geojson['features'].append(feature)
	intersection_path = os.path.join(output_dir, f"{area_name}_final_intersection.geojson")
	with open(intersection_path, 'w', encoding='utf-8') as f:
		json.dump(intersection_geojson, f, ensure_ascii=False, indent=2)
	print(f"✅ 最终方案交集GeoJSON已保存到: {intersection_path}")

	print("\n🎉 规划流程执行完毕！")

	return {
		'success': optimal_plan is not None,  # 'success' 仅在达到目标时为 True
		'report': report,
		'map_path': map_path,
		'intersection_geojson_path': intersection_path
	}

def main():
	"""主函数，用于演示如何调用通用规划器"""

	# --- 准备输入数据 ---
	# 1. TLE 数据

	tle_data = get_valid_satellite_tle_as_dict(satellite_db_path='D:\GeoSensingAPI\data\satellite_data.db',
	                                           mission_theme='Land cover',
	                                           sensor_type='Optical Sensor')

	# 2. 观测区域 GeoJSON 文件路径
	# 创建一个示例GeoJSON文件用于演示
	wuhan_geojson_path = "D:\GeoSensingAPI\geojson\Wuhan.geojson"

	# 3. 时间范围
	start_time = "2025-08-1 00:00:00.000"
	end_time = "2025-08-1 23:59:59.000"

	# --- 调用通用规划函数 ---
	planning_results = plan_satellite_observation(
		target_geojson_path=wuhan_geojson_path,
		tle_dict=tle_data,
		start_time=start_time,
		end_time=end_time,
		target_coverage=0.95,  # 设定一个较高的目标覆盖率
		fov=10.0,
		output_dir="Wuhan_Planning_Results"  # 指定本次规划的输出目录
	)

	# --- 打印最终推荐方案 ---
	if planning_results and planning_results['success']:
		plan = planning_results['report']['optimal_plan']
		print("\n" + "=" * 60)
		print("🏆 最终推荐方案 🏆")
		print("=" * 60)
		print(f"  - 类型: {'单星覆盖' if plan['type'] == 'single' else '多星组合'}")
		print(f"  - 卫星: {', '.join(plan['satellites'])}")
		print(f"  - 预估覆盖率: {plan['coverage']:.2%}")
		print(f"  - 详细结果见: '{os.path.abspath('Wuhan_Planning_Results')}'")
		print("=" * 60)
	else:
		print("\n❌ 未能找到满足覆盖率目标的方案。")


if __name__ == "__main__":
	main()
