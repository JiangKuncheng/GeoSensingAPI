import json
import numpy as np
from datetime import datetime, timedelta
import geojson
from shapely.geometry import shape
from shapely.ops import unary_union

# 导入您已经写好的函数
from satelliteTool.get_observation_lace import get_coverage_lace
from satelliteTool.get_observation_overlap import get_observation_overlap


# =============================================================================
# PART 2: DOCI SUB-CAPABILITIES FRAMEWORK
# =============================================================================

def get_theme_relevance_from_oscar(sensor_name, task_theme):
	"""模拟查询OSCAR数据库以获取专题相关性。"""
	print(f"  - 正在模拟查询 Theme (Th)...")
	# 根据传感器名称和任务主题返回相关性
	theme_mapping = {
		'LANDSAT': 'high',
		'SENTINEL': 'high', 
		'GAOFEN': 'medium',
		'ZY': 'medium',
		'HJ': 'useful'
	}
	
	for key, value in theme_mapping.items():
		if key in sensor_name.upper():
			relevance = value
			break
	else:
		relevance = 'medium'  # 默认值
		
	print(f"    * Theme Relevance = '{relevance}'")
	return relevance


def get_cloudiness_from_owm(target_geojson, task_period):
	"""模拟查询天气服务以获取云量预报。"""
	print(f"  - 正在模拟查询 Radiation (Ra)...")
	# 模拟8月份武汉地区的云量情况
	cloudiness = 0.25  # 示例值：25%的云量（8月份多云天气）
	print(f"    * Cloudiness = {cloudiness:.2%}")
	return cloudiness


def calculate_theme(relevance):
	theme_map = {'primary': 1.0, 'high': 0.8, 'medium': 0.6, 'useful': 0.4, 'marginal': 0.2}
	return theme_map.get(relevance.lower(), 0.0)


def calculate_radiation(cloudiness):
	return 1.0 - cloudiness


def calculate_accuracy(sensor_quantization, max_quantization):
	if max_quantization == 0: return 0
	return sensor_quantization / max_quantization


def calculate_spacetime(sensor_attrs, task_reqs, weights):
	print(f"  - 正在计算 SpaceTime (ST)...")
	indicators = ['spatial_res', 'temporal_res']
	grades = np.array([1.0, 0.5, 0.1])
	R = np.zeros((2, 3))
	for i, indicator in enumerate(indicators):
		x = sensor_attrs[indicator]
		t, b, g = task_reqs[indicator]
		is_inverse = "res" in indicator
		_x, _t, _b, _g = (-x, -t, -b, -g) if is_inverse else (x, t, b, g)
		if _x >= _g:
			mu1 = 1.0
		elif _g > _x >= _b:
			mu1 = (_x - _b) / (_g - _b)
		else:
			mu1 = 0.0
		if _b > _x >= _t:
			mu2 = (_x - _t) / (_b - _t)
		elif _g > _x >= _b:
			mu2 = (_g - _x) / (_g - _b)
		else:
			mu2 = 0.0
		if _x < _t:
			mu3 = 1.0
		elif _b > _x >= _t:
			mu3 = (_b - _x) / (_b - _t)
		else:
			mu3 = 0.0
		R[i, :] = [mu1, mu2, mu3]
	W = np.array(weights)
	B = W @ R
	space_time_value = np.sum(B * grades)
	print(f"    * SpaceTime (ST) = {space_time_value:.3f}")
	return space_time_value


# =============================================================================
# PART 3: MAIN DOCI CALCULATION ORCHESTRATOR
# =============================================================================

def calculate_doci_for_task(sensor_properties, task_requirements, all_sensors):
	"""
	为单个传感器和单个任务计算完整的DOCI及其所有子能力。
	"""
	name = sensor_properties['name']
	print(f"\n-> 正在为传感器 '{name}' 评估任务 '{task_requirements['description']}'...")

	# 1. Co: Coverage - 使用get_observation_lace获取卫星足迹，然后计算覆盖率
	print("  - 正在计算 Coverage (Co)...")
	
	# 构建TLE字典格式
	tle_dict = {name: sensor_properties['tle_str']}
	
	# 首先使用get_observation_lace获取卫星足迹
	coverage_geojson = get_coverage_lace(
		tle_dict=tle_dict,
		start_time_str=task_requirements['start_time'],
		end_time_str=task_requirements['end_time'],
		fov=sensor_properties['fov'],
		interval_seconds=600  # 10分钟间隔
	)
	
	# 然后使用get_observation_overlap计算覆盖率
	overlap_results = get_observation_overlap(
		tle_dict=tle_dict,
		start_time_str=task_requirements['start_time'],
		end_time_str=task_requirements['end_time'],
		target_geojson=task_requirements['geojson_area'],
		fov=sensor_properties['fov'],
		interval_seconds=600  # 10分钟间隔
	)
	
	# 获取覆盖率
	Co = overlap_results.get(name, 0.0)
	print(f"    * Coverage (Co) = {Co:.3f}")
	print(f"    * 生成了 {len(coverage_geojson['features'])} 个足迹点")

	# 2. Th: Theme
	relevance = get_theme_relevance_from_oscar(name, task_requirements['theme'])
	Th = calculate_theme(relevance)

	# 3. Ra: Radiation
	cloudiness = get_cloudiness_from_owm(task_requirements['geojson_area'], task_requirements['start_time'])
	Ra = calculate_radiation(cloudiness)

	if Co <= 0 or Th == 0 or Ra == 0:
		print(f"   ! 传感器 '{name}' 的先决条件不满足 (Co={Co:.2f}, Th={Th:.2f}, Ra={Ra:.2f})，DOCI=0")
		return {'Co': Co, 'Th': Th, 'Ra': Ra, 'ST': 0, 'Ac': 0, 'DOCI': 0}

	# 4. ST: SpaceTime
	ST = calculate_spacetime(sensor_properties, task_requirements['requirements'], task_requirements['ahp_weights'])

	# 5. Ac: Accuracy
	print(f"  - 正在计算 Accuracy (Ac)...")
	max_q = max(s['quantization_level'] for s in all_sensors.values())
	Ac = calculate_accuracy(sensor_properties['quantization_level'], max_q)
	print(f"    * Accuracy (Ac) = {Ac:.3f}")

	# 最终DOCI计算
	doci_value = 0.25 * ((Co + ST) + (Th + Ra) * Ac)

	results = {'Co': Co, 'Th': Th, 'Ra': Ra, 'ST': ST, 'Ac': Ac, 'DOCI': doci_value}
	print(f"   * DOCI for '{name}' = {doci_value:.3f}")
	return results


def calculate_doci_for_all_sensors(sensors_data, task_requirements):
	"""
	为所有传感器计算DOCI值
	"""
	print("=" * 80)
	print("开始计算所有传感器的DOCI值")
	print("=" * 80)
	
	results = {}
	
	for sensor_name, sensor_props in sensors_data.items():
		try:
			result = calculate_doci_for_task(sensor_props, task_requirements, sensors_data)
			results[sensor_name] = result
		except Exception as e:
			print(f"计算传感器 '{sensor_name}' 的DOCI时出错: {e}")
			results[sensor_name] = {'Co': 0, 'Th': 0, 'Ra': 0, 'ST': 0, 'Ac': 0, 'DOCI': 0}
	
	return results


# =============================================================================
# PART 4: EXAMPLE USAGE
# =============================================================================

if __name__ == '__main__':
	# 加载TLE数据
	with open('satelliteTool/tle_data.json', 'r', encoding='utf-8') as f:
		tle_data = json.load(f)
	
	# 定义传感器属性
	sensors_data = {}
	for name, tle_str in tle_data.items():
		# 根据卫星类型设置不同的属性
		if 'LANDSAT' in name:
			spatial_res = 30  # 30米空间分辨率
			temporal_res = 16  # 16天重访周期
			quantization = 12  # 12位量化
			fov = 15.0  # 15度视场角
		elif 'SENTINEL' in name:
			spatial_res = 10  # 10米空间分辨率
			temporal_res = 5   # 5天重访周期
			quantization = 12  # 12位量化
			fov = 20.0  # 20度视场角
		elif 'GAOFEN' in name:
			spatial_res = 8    # 8米空间分辨率
			temporal_res = 4   # 4天重访周期
			quantization = 10  # 10位量化
			fov = 25.0  # 25度视场角
		elif 'ZY' in name:
			spatial_res = 5    # 5米空间分辨率
			temporal_res = 3   # 3天重访周期
			quantization = 10  # 10位量化
			fov = 30.0  # 30度视场角
		elif 'HJ' in name:
			spatial_res = 30   # 30米空间分辨率
			temporal_res = 4   # 4天重访周期
			quantization = 8   # 8位量化
			fov = 35.0  # 35度视场角
		else:
			spatial_res = 20   # 默认值
			temporal_res = 10  # 默认值
			quantization = 10  # 默认值
			fov = 20.0  # 默认值
		
		sensors_data[name] = {
			'name': name,
			'tle_str': tle_str,
			'spatial_res': spatial_res,
			'temporal_res': temporal_res,
			'quantization_level': quantization,
			'fov': fov
		}
	
	# 定义任务需求（武汉市区域）
	wuhan_geojson = {
		"type": "FeatureCollection",
		"features": [{
			"type": "Feature",
			"properties": {},
			"geometry": {
				"type": "Polygon",
				"coordinates": [[
					[114.0, 30.0],
					[114.8, 30.0],
					[114.8, 30.8],
					[114.0, 30.8],
					[114.0, 30.0]
				]]
			}
		}]
	}
	
	task_requirements = {
		'description': '武汉市区域环境监测任务',
		'theme': 'environmental_monitoring',
		'start_time': '2025-08-05 00:00:00.000',
		'end_time': '2025-08-10 23:59:59.000',
		'geojson_area': wuhan_geojson,
		'requirements': {
			'spatial_res': (30, 20, 10),  # (threshold, baseline, goal)
			'temporal_res': (10, 5, 2)     # (threshold, baseline, goal)
		},
		'ahp_weights': [0.6, 0.4]  # 空间分辨率权重0.6，时间分辨率权重0.4
	}
	
	print("武汉市DOCI计算示例")
	print(f"时间窗口: {task_requirements['start_time']} 到 {task_requirements['end_time']}")
	print(f"目标区域: 武汉市 ({wuhan_geojson['features'][0]['geometry']['coordinates'][0][0][0]:.1f}°E, {wuhan_geojson['features'][0]['geometry']['coordinates'][0][0][1]:.1f}°N)")
	print(f"传感器数量: {len(sensors_data)}")
	print()
	
	# 计算所有传感器的DOCI值
	results = calculate_doci_for_all_sensors(sensors_data, task_requirements)
	
	# 按DOCI值排序并显示结果
	print("\n" + "=" * 80)
	print("DOCI计算结果汇总（按DOCI值降序排列）")
	print("=" * 80)
	
	sorted_results = sorted(results.items(), key=lambda x: x[1]['DOCI'], reverse=True)
	
	print(f"{'传感器名称':<20} {'覆盖率(Co)':<10} {'专题性(Th)':<10} {'辐射性(Ra)':<10} {'时空性(ST)':<10} {'精度性(Ac)':<10} {'DOCI':<10}")
	print("-" * 90)
	
	for sensor_name, result in sorted_results:
		print(f"{sensor_name:<20} {result['Co']:<10.3f} {result['Th']:<10.3f} {result['Ra']:<10.3f} {result['ST']:<10.3f} {result['Ac']:<10.3f} {result['DOCI']:<10.3f}")
	
	# 保存结果到文件
	output_file = 'wuhan_doci_results_2025-08-05_to_08-10.json'
	with open(output_file, 'w', encoding='utf-8') as f:
		json.dump(results, f, ensure_ascii=False, indent=2)
	
	print(f"\n✅ 结果已保存到文件: {output_file}")
	
	# 显示最佳传感器
	best_sensor = sorted_results[0]
	print(f"\n🏆 最佳传感器: {best_sensor[0]} (DOCI = {best_sensor[1]['DOCI']:.3f})")
	print(f"   该传感器在指定时间窗口内对武汉市的覆盖能力最强")
	