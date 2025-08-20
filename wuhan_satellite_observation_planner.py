#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
武汉市卫星观测规划器 (精简版)
功能：分析与武汉市相交的卫星，并规划最优覆盖方案
"""

import json
from datetime import datetime
from itertools import combinations
# 导入必要的地理信息处理库
from shapely.geometry import shape
from shapely.ops import unary_union, transform
from pyproj import Proj, Transformer

# 导入您已经写好的工具函数
from satelliteTool.get_observation_lace import get_coverage_lace
from satelliteTool.get_observation_overlap import get_observation_overlap
from GeoPandasTool.intersects import intersects
from GeoPandasTool.is_valid import is_valid
import folium


class WuhanSatelliteObservationPlanner:
	"""武汉市卫星观测规划器"""

	def __init__(self):
		self.final_coverage_dict_geom = None
		self.final_coverage_results_geom = None
		self.tle_data = {}
		self.wuhan_geojson = None

	def load_tle_data(self):
		"""加载TLE数据"""
		print("正在加载TLE数据...")
		try:
			with open('satelliteTool/tle_data.json', 'r', encoding='utf-8') as f:
				self.tle_data = json.load(f)
			print(f"✅ 成功加载 {len(self.tle_data)} 颗卫星的TLE数据")
			return True
		except Exception as e:
			print(f"❌ 加载TLE数据失败: {e}")
			return False

	def define_wuhan_area(self):
		"""定义武汉市区域"""
		print("正在定义武汉市区域...")
		self.wuhan_geojson = {
			"type": "FeatureCollection",
			"features": [{
				"type": "Feature", "properties": {"name": "武汉市"},
				"geometry": {
					"type": "Polygon",
					"coordinates": [[[114.0, 30.0], [114.8, 30.0], [114.8, 30.8], [114.0, 30.8], [114.0, 30.0]]]
				}
			}]
		}
		print("✅ 武汉市区域定义完成 (经度 114.0°-114.8°, 纬度 30.0°-30.8°)")

	def get_satellite_footprints(self, start_time, end_time, fov=10.0, interval_seconds=600):
		"""获取所有卫星的覆盖足迹"""
		print(f"\n正在获取卫星覆盖足迹 (时间: {start_time} 到 {end_time})...")
		try:
			coverage_dict = get_coverage_lace(
				tle_dict=self.tle_data, start_time_str=start_time, end_time_str=end_time,
				fov=fov, interval_seconds=interval_seconds
			)
			total_features = sum(len(geojson['features']) for geojson in coverage_dict.values())
			print(f"✅ 成功生成 {total_features} 个足迹点，涉及 {len(coverage_dict)} 颗卫星")
			return coverage_dict
		except Exception as e:
			print(f"❌ 获取卫星足迹失败: {e}")
			return None

	def filter_intersecting_satellites(self, coverage_dict):
		"""筛选与武汉市相交的卫星"""
		print("\n正在筛选与武汉市相交的卫星...")
		if not coverage_dict:
			return []

		wuhan_geojson_str = json.dumps(self.wuhan_geojson)
		intersecting_satellites = []

		for satellite_name, satellite_geojson in coverage_dict.items():
			if not satellite_geojson.get('features'):
				continue
			try:
				if any(intersects(json.dumps(satellite_geojson), wuhan_geojson_str)):
					intersecting_satellites.append(satellite_name)
					print(f"  - ✅ {satellite_name}: 与武汉市相交")
			except Exception as e:
				print(f"  - ❌ 检查卫星 {satellite_name} 时出错: {e}")

		print(f"\n✅ 筛选完成，找到 {len(intersecting_satellites)} 颗相交卫星")
		return intersecting_satellites

	def calculate_coverage_for_satellites(self, intersecting_satellites, start_time, end_time, fov=10.0,
	                                      interval_seconds=600):
		"""计算每个相交卫星的覆盖率"""
		print(f"\n正在计算卫星覆盖率...")
		if not intersecting_satellites:
			return {}

		filtered_tle_dict = {name: self.tle_data[name] for name in intersecting_satellites}
		try:
			coverage_results = get_observation_overlap(
				tle_dict=filtered_tle_dict, start_time_str=start_time, end_time_str=end_time,
				target_geojson=self.wuhan_geojson, fov=fov, interval_seconds=interval_seconds
			)
			print(f"✅ 覆盖率计算完成")
			for satellite, data in coverage_results.items():
				print(
					f"   - {satellite}: 覆盖率 {data['coverage_ratio']:.2%}, 相交足迹: {len(data['intersection_footprints'])}个")
			return coverage_results
		except Exception as e:
			print(f"❌ 计算覆盖率失败: {e}")
			return {}

	def find_optimal_coverage_plan(self, coverage_results, target_coverage=0.9):
		"""寻找最优覆盖方案"""
		print(f"\n正在寻找最优覆盖方案 (目标: {target_coverage:.0%})...")
		if not coverage_results: return None

		# 检查单个卫星方案
		for satellite, data in coverage_results.items():
			if data['coverage_ratio'] >= target_coverage:
				print(f"✅ 找到单个卫星解决方案: {satellite} (覆盖率: {data['coverage_ratio']:.2%})")
				return {'type': 'single', 'satellites': [satellite], 'coverage': data['coverage_ratio']}

		# 寻找组合方案
		print("   没有单个卫星能达到目标，正在寻找组合方案...")
		sorted_satellites = sorted(coverage_results.keys(), key=lambda sat: coverage_results[sat]['coverage_ratio'],
		                           reverse=True)

		# 定义用于面积计算的投影
		wgs84_proj = Proj('epsg:4326')
		equal_area_proj = Proj('+proj=moll')  # Mollweide等面积投影
		transformer = Transformer.from_proj(wgs84_proj, equal_area_proj, always_xy=True)
		wuhan_shape = shape(self.wuhan_geojson['features'][0]['geometry'])
		wuhan_area = transform(transformer.transform, wuhan_shape).area

		for combination_size in range(2, min(5, len(sorted_satellites) + 1)):
			for combo in combinations(sorted_satellites, combination_size):
				combo_coverage = self._calculate_combined_coverage(list(combo), coverage_results, transformer,
				                                                   wuhan_area)
				if combo_coverage >= target_coverage:
					print(f"✅ 找到最佳组合方案: {list(combo)} (覆盖率: {combo_coverage:.2%})")
					return {'type': 'combination', 'satellites': list(combo), 'coverage': combo_coverage}

		print("❌ 无法找到满足要求的卫星组合")
		return None

	def _calculate_combined_coverage(self, satellite_list, coverage_results, transformer, target_area):
		"""【已优化】精确计算卫星组合的并集覆盖率"""
		all_footprints = []
		for satellite in satellite_list:
			footprint_features = coverage_results[satellite]['intersection_footprints']
			for feature in footprint_features:
				all_footprints.append(shape(feature['geometry']))

		if not all_footprints: return 0.0

		# 合并所有足迹并计算投影后的面积
		merged_footprints = unary_union(all_footprints)
		projected_merged = transform(transformer.transform, merged_footprints)
		return projected_merged.area / target_area

	def create_coverage_visualization(self, coverage_results, coverage_dict,
	                                  output_file="wuhan_satellite_coverage_map.html"):
		"""
		【已修改】创建交互式卫星覆盖可视化地图。
		每个卫星的覆盖区域都是一个独立的、可在图层控件中切换的图层。
		"""
		if not folium:
			print("Folium库未安装，无法创建地图。")
			return None

		print("\n=== 正在创建交互式可视化地图 ===")
		try:
			m = folium.Map(location=[30.4, 114.4], zoom_start=9, tiles="CartoDB positron")

			# 1. 绘制武汉市边界 (作为固定图层)
			folium.GeoJson(self.wuhan_geojson, name='武汉市边界',
			               style_function=lambda x: {'color': 'black', 'weight': 3, 'fillOpacity': 0.1,
			                                         'fillColor': 'gray'},
			               tooltip='武汉市研究区域').add_to(m)

			# 2. 【修改】为每个卫星创建独立的、可切换的图层
			# 定义一个颜色列表，为不同卫星分配不同颜色，方便区分
			colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6',
			          '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#800000', '#aaffc3', '#000075']

			# (可选) 按覆盖率从高到低排序，让最重要的卫星显示在列表顶部
			sorted_results = sorted(coverage_results.items(), key=lambda item: item[1]['coverage_ratio'], reverse=True)

			for i, (satellite_name, data) in enumerate(sorted_results):
				if data.get('intersection_footprints'):
					# 为每个卫星创建一个FeatureGroup，它将作为独立的图层
					# 在图层名称中直接显示覆盖率，一目了然
					layer_name = f"{satellite_name} ({data['coverage_ratio']:.1%})"
					satellite_layer = folium.FeatureGroup(name=layer_name, show=True)

					# 从颜色列表中循环选择一个颜色
					color = colors[i % len(colors)]

					# 将该卫星的所有相交足迹添加到它的专属图层中
					folium.GeoJson(
						{"type": "FeatureCollection", "features": data['intersection_footprints']},
						style_function=lambda x, c=color: {'color': c, 'weight': 2, 'fillColor': c, 'fillOpacity': 0.5},
						tooltip=f"<b>{satellite_name}</b><br>覆盖率: {data['coverage_ratio']:.2%}"
					).add_to(satellite_layer)

					# 将这个卫星图层添加到主地图
					satellite_layer.add_to(m)

			# 3. 【修改】移除静态HTML图例，只保留图层控制器
			# folium.LayerControl会自动识别所有添加的独立图层，并生成一个可勾选的列表
			folium.LayerControl(collapsed=False).add_to(m)
			m.save(output_file)
			print(f"✅ 交互式可视化地图已保存到: {output_file}")
			return output_file

		except Exception as e:
			print(f"❌ 生成可视化地图时出错: {e}")
			return None

	def generate_observation_plan(self, start_time, end_time, fov=45.0, interval_seconds=600):
		"""生成完整的观测规划"""
		print("=" * 60)
		print("武汉市卫星观测规划生成器")
		print("=" * 60)

		if not self.load_tle_data():
			return None
		self.define_wuhan_area()

		coverage_dict = self.get_satellite_footprints(start_time, end_time, fov, interval_seconds)
		if not coverage_dict:
			return None

		intersecting_satellites = self.filter_intersecting_satellites(coverage_dict)
		if not intersecting_satellites:
			return None

		coverage_results = self.calculate_coverage_for_satellites(
			intersecting_satellites, start_time, end_time, fov, interval_seconds
		)

		optimal_plan = self.find_optimal_coverage_plan(coverage_results)

		# 生成最终报告
		final_report = {
			'planning_period': {'start_time': start_time, 'end_time': end_time},
			'target_area': '武汉市',
			'intersecting_satellites_count': len(intersecting_satellites),
			'coverage_by_satellite': {k: v['coverage_ratio'] for k, v in coverage_results.items()},
			'optimal_plan': optimal_plan,
			'generation_time': datetime.now().isoformat()
		}

		# 保存原始几何数据用于可视化
		self.final_coverage_results_geom = coverage_results
		self.final_coverage_dict_geom = coverage_dict

		return final_report


def main():
	"""主函数"""
	planner = WuhanSatelliteObservationPlanner()

	start_time = "2025-08-01 00:00:00.000"
	end_time = "2025-08-01 23:59:59.000"

	results = planner.generate_observation_plan(
		start_time=start_time, end_time=end_time,
		fov=20.0, interval_seconds=600
	)

	if results:
		# 保存JSON报告
		output_filename = 'wuhan_satellite_observation_plan.json'
		with open(output_filename, 'w', encoding='utf-8') as f:
			json.dump(results, f, ensure_ascii=False, indent=2)
		print(f"\n✅ 规划报告已保存到: {output_filename}")

		# 创建可视化地图
		planner.create_coverage_visualization(
			planner.final_coverage_results_geom,
			planner.final_coverage_dict_geom
		)

		# 打印最终推荐方案
		print("\n" + "=" * 60)
		print("🏆 最终推荐方案 🏆")
		print("=" * 60)
		if results['optimal_plan']:
			plan = results['optimal_plan']
			print(f"  - 类型: {'单星覆盖' if plan['type'] == 'single' else '多星组合'}")
			print(f"  - 卫星: {', '.join(plan['satellites'])}")
			print(f"  - 预估覆盖率: {plan['coverage']:.2%}")
		else:
			print("  ❌ 未能找到满足覆盖率目标的方案。")
		print("=" * 60)
	else:
		print("\n❌ 观测规划生成失败")


if __name__ == "__main__":
	main()
