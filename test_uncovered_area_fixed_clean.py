#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：测试difference.py计算后的未覆盖区域处理结果 + 可视化
修复版本：先清理无效几何图形，再进行difference计算
"""

import json
import sys
import os

# 添加路径
sys.path.append('satelliteTool')
sys.path.append('GeoPandasTool')

from satelliteTool.get_observation_lace import get_coverage_lace
from satelliteTool.get_observation_overlap import get_observation_overlap
from GeoPandasTool.difference import difference
from GeoPandasTool.is_valid import is_valid
from GeoPandasTool.is_valid_reason import is_valid_reason


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


def clean_invalid_geometries(coverage_geojson):
	"""清理无效的几何图形，只保留有效的"""
	print("正在清理无效的几何图形...")

	try:
		# 转换为字符串以使用is_valid函数
		coverage_str = json.dumps(coverage_geojson)

		# 检查几何图形合法性
		validity_results = is_valid(coverage_str)
		validity_reasons = is_valid_reason(coverage_str)

		# 统计有效和无效的几何图形
		valid_count = sum(validity_results)
		invalid_count = len(validity_results) - valid_count

		print(f"原始几何图形数量: {len(validity_results)}")
		print(f"有效几何图形数量: {valid_count}")
		print(f"无效几何图形数量: {invalid_count}")

		if invalid_count > 0:
			print("\n前5个无效几何图形的原因:")
			for i, (is_valid_flag, reason) in enumerate(zip(validity_results, validity_reasons)):
				if not is_valid_flag and i < 5:
					print(f"  特征 {i}: {reason}")

		# 只保留有效的几何图形
		cleaned_features = []
		for i, feature in enumerate(coverage_geojson['features']):
			if validity_results[i]:
				cleaned_features.append(feature)
			else:
				print(f"移除无效特征 {i}: {validity_reasons[i]}")

		cleaned_coverage = {
			"type": "FeatureCollection",
			"features": cleaned_features
		}

		print(f"清理后几何图形数量: {len(cleaned_features)}")

		return cleaned_coverage

	except Exception as e:
		print(f"❌ 清理几何图形时出错: {e}")
		import traceback
		traceback.print_exc()
		return coverage_geojson  # 如果清理失败，返回原始数据


def test_satellite_coverage():
	"""测试卫星覆盖分析"""
	print("=" * 60)
	print("步骤1: 测试卫星覆盖分析")
	print("=" * 60)

	# 加载数据
	tle_data = load_tle_data()
	wuhan_boundary = load_wuhan_boundary()

	print(f"TLE数据卫星数量: {len(tle_data)}")
	print(f"武汉市边界特征数量: {len(wuhan_boundary['features'])}")

	# 获取卫星覆盖轨迹
	print("\n正在计算卫星覆盖轨迹...")
	coverage = get_coverage_lace(
		tle_dict=tle_data,
		start_time_str="2025-08-01 00:00:00.000",
		end_time_str="2025-08-01 23:59:59.000",
		fov=10.0,
		interval_seconds=600
	)

	print(f"卫星覆盖轨迹特征数量: {len(coverage['features'])}")

	# 清理无效的几何图形
	cleaned_coverage = clean_invalid_geometries(coverage)

	# 计算覆盖率
	print("\n正在计算覆盖率...")
	overlap_results = get_observation_overlap(
		tle_dict=tle_data,
		start_time_str="2025-08-01 00:00:00.000",
		end_time_str="2025-08-01 23:59:59.000",
		target_geojson=wuhan_boundary,
		fov=10.0,
		interval_seconds=600
	)

	total_coverage = sum(overlap_results.values()) if overlap_results else 0
	print(f"卫星总覆盖率: {total_coverage:.2%}")

	return cleaned_coverage, overlap_results, total_coverage


def test_uncovered_area_calculation(wuhan_boundary, coverage):
	"""测试未覆盖区域计算"""
	print("\n" + "=" * 60)
	print("步骤2: 测试未覆盖区域计算")
	print("=" * 60)

	# 保存清理后的卫星覆盖数据到文件
	with open("test_satellite_coverage_cleaned.geojson", 'w') as f:
		json.dump(coverage, f, indent=2)
	print("✅ 清理后的卫星覆盖数据已保存到: test_satellite_coverage_cleaned.geojson")

	# 保存武汉市边界到文件
	with open("test_wuhan_boundary.geojson", 'w') as f:
		json.dump(wuhan_boundary, f, indent=2)
	print("✅ 武汉市边界已保存到: test_wuhan_boundary.geojson")

	# 使用difference计算未覆盖区域
	print("\n正在使用difference.py计算未覆盖区域...")
	try:
		coverage_str = json.dumps(coverage)
		wuhan_str = json.dumps(wuhan_boundary)

		print(f"清理后卫星覆盖数据字符串长度: {len(coverage_str)}")
		print(f"武汉市边界字符串长度: {len(wuhan_str)}")

		uncovered_geojson_str = difference(wuhan_str, coverage_str)
		uncovered_geojson = json.loads(uncovered_geojson_str)

		print(f"✅ 未覆盖区域计算成功！")
		print(f"未覆盖区域特征数量: {len(uncovered_geojson['features'])}")

		# 保存未覆盖区域到文件
		with open("test_uncovered_area.geojson", 'w') as f:
			json.dump(uncovered_geojson, f, indent=2)
		print("✅ 未覆盖区域已保存到: test_uncovered_area.geojson")

		return uncovered_geojson

	except Exception as e:
		print(f"❌ 计算未覆盖区域时出错: {e}")
		import traceback
		traceback.print_exc()
		return None


def generate_visualization_map(wuhan_boundary, satellite_coverage, uncovered_area, total_coverage):
	"""生成可视化地图，显示武汉市边界、卫星覆盖区域和未覆盖区域"""
	print("=== 生成可视化地图 ===")

	try:
		import folium

		# 计算地图中心点
		center_lat = 30.547
		center_lon = 114.405

		# 创建地图
		m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

		# 1. 绘制总任务区域（武汉市边界）
		folium.GeoJson(
			wuhan_boundary,
			style_function=lambda x: {
				'color': 'black', 'weight': 3, 'fillOpacity': 0.1, 'fillColor': 'black'
			},
			name='总任务区域（武汉市）',
			tooltip='总任务区域（武汉市）',
			show=True
		).add_to(m)

		# 2. 绘制卫星覆盖区域
		if satellite_coverage and satellite_coverage.get('features'):
			folium.GeoJson(
				satellite_coverage,
				style_function=lambda x: {
					'color': 'blue', 'weight': 2, 'fillOpacity': 0.3, 'fillColor': 'blue'
				},
				name='卫星覆盖区域',
				tooltip=f'卫星覆盖区域（覆盖率: {total_coverage:.2%}）',
				show=True
			).add_to(m)

		# 3. 绘制未覆盖区域
		if uncovered_area and uncovered_area.get('features'):
			folium.GeoJson(
				uncovered_area,
				style_function=lambda x: {
					'color': 'yellow', 'weight': 2, 'fillOpacity': 0.4, 'fillColor': 'yellow'
				},
				name='未覆盖区域',
				tooltip='卫星未覆盖区域（需要无人机和地面站补全）',
				show=True
			).add_to(m)

				# 添加图例（调整到右下角，避免遮挡）
		legend_html = '''
		<div style="position: fixed; 
					bottom: 50px; right: 50px; width: 250px; height: 150px; 
					background-color: white; border:2px solid grey; z-index:9999; 
					font-size:14px; padding: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
			<p><b>图例</b></p>
			<p><span style="color:black;">⬛</span> 总任务区域（武汉市）</p>
			<p><span style="color:blue;">⬛</span> 卫星覆盖区域</p>
			<p><span style="color:yellow;">⬛</span> 未覆盖区域</p>
		</div>
		'''
		m.get_root().html.add_child(folium.Element(legend_html))
		
		# 添加图层控制（调整到左上角）
		folium.LayerControl(collapsed=False, position='topleft').add_to(m)

		# 保存地图
		output_file = "test_coverage_visualization_fixed.html"
		m.save(output_file)
		print(f"✅ 可视化地图已保存到: {output_file}")

				# 添加统计信息（调整到右上角，与图例不重叠）
		stats_html = f'''
		<div style="position: fixed; 
					top: 50px; right: 50px; width: 300px; height: 200px; 
					background-color: white; border:2px solid grey; z-index:9999; 
					font-size:14px; padding: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
			<p><b>覆盖统计</b></p>
			<p>卫星覆盖率: {total_coverage:.2%}</p>
			<p>卫星覆盖特征: {len(satellite_coverage['features'])}</p>
			<p>未覆盖特征: {len(uncovered_area['features'])}</p>
			<p>武汉市边界特征: {len(wuhan_boundary['features'])}</p>
		</div>
		'''
		m.get_root().html.add_child(folium.Element(stats_html))

		# 重新保存包含统计信息的地图
		m.save(output_file)

		return output_file

	except ImportError:
		print("❌ 缺少folium库，无法生成可视化地图")
		print("请安装: pip install folium")
		return None
	except Exception as e:
		print(f"❌ 生成可视化地图时出错: {e}")
		import traceback
		traceback.print_exc()
		return None


def main():
	"""主函数"""
	print("🧪 未覆盖区域计算测试脚本 + 可视化（修复版本）")
	print("=" * 60)

	# 步骤1: 测试卫星覆盖分析（包含几何图形清理）
	coverage, overlap_results, total_coverage = test_satellite_coverage()

	# 步骤2: 测试未覆盖区域计算
	wuhan_boundary = load_wuhan_boundary()
	uncovered_area = test_uncovered_area_calculation(wuhan_boundary, coverage)

	# 总结
	print("\n" + "=" * 60)
	print("测试总结")
	print("=" * 60)
	print(f"卫星覆盖率: {total_coverage:.2%}")
	print(f"清理后卫星覆盖特征数量: {len(coverage['features'])}")
	if uncovered_area:
		print(f"未覆盖区域特征数量: {len(uncovered_area['features'])}")
	else:
		print("未覆盖区域计算失败")

	print(f"\n生成的文件:")
	print("  - test_satellite_coverage_cleaned.geojson (清理后的卫星覆盖数据)")
	print("  - test_wuhan_boundary.geojson (武汉市边界)")
	if uncovered_area:
		print("  - test_uncovered_area.geojson (未覆盖区域)")

	print("\n请检查这些文件，了解各个步骤的输出结果。")

	# 生成可视化地图
	if uncovered_area:
		print("\n正在生成可视化地图...")
		generate_visualization_map(wuhan_boundary, coverage, uncovered_area, total_coverage)
	else:
		print("❌ 无法生成可视化地图，因为未覆盖区域计算失败")


if __name__ == "__main__":
	main()
