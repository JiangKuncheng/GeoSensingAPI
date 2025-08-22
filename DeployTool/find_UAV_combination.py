# -*- coding: utf-8 -*-
"""
PROJECT_NAME: Gaode_POI.py 
FILE_NAME: find_UAV_combination 
AUTHOR: welt 
E_MAIL: tjlwelt@foxmail.com
DATE: 2025-08-20 
"""

import sqlite3
import pandas as pd


def find_drone_combination(required_area_sq_km, db_path='DeployTool/UAV_data.db'):
	"""
	根据需要观测的面积，从无人机数据库中查询能满足要求无人机组合。

	Args:
		required_area_sq_km (float): 需要观测的总面积，单位为平方公里。
		db_path (str): 无人机数据库文件的路径。

	Returns:
		dict: 一个字典，包含被选中的无人机。键是生成的无人机ID，值是包含该无人机详细信息的字典。
			  如果数据库中没有任何无人机，则返回一个空字典。
	"""
	try:
		# 连接到SQLite数据库
		conn = sqlite3.connect(db_path)
		# 使用pandas读取数据到DataFrame
		df = pd.read_sql_query("SELECT * FROM drones_final", conn)
		conn.close()
	except sqlite3.Error as e:
		print(f"数据库连接或查询错误: {e}")
		return {}
	except pd.io.sql.DatabaseError:
		print(f"错误：在数据库 '{db_path}' 中找不到 'drones_final' 表。")
		return {}

	if df.empty:
		print("数据库中没有无人机数据。")
		return {}

	# --- 数据处理和计算 ---
	# 1. 计算每款无人机单次飞行的覆盖面积（平方米）
	# 覆盖面积 = 飞行时长(秒) * 飞行速度(米/秒) * 扫描宽度(米)
	df['coverage_sq_m'] = df['flight_duration_s'] * df['average_speed_mps'] * df['scan_width_m']

	# 2. 将需求面积从平方公里转换为平方米
	required_area_sq_m = required_area_sq_km * 1_000_000

	# 3. 筛选出有有效覆盖能力的无人机，并按覆盖能力从高到低排序
	df_capable = df[df['coverage_sq_m'] > 0].sort_values(by='coverage_sq_m', ascending=False)

	if df_capable.empty:
		print("数据库中没有具备有效覆盖能力的无人机。")
		return {}

	# --- 贪心算法选择无人机 ---
	drone_fleet = {}
	total_coverage_sq_m = 0
	drone_counter = 1

	# 获取最高效的无人机（覆盖面积最大的那款）
	best_drone = df_capable.iloc[0]

	while total_coverage_sq_m < required_area_sq_m:
		# 将最高效的无人机添加到机队中
		total_coverage_sq_m += best_drone['coverage_sq_m']

		# 为本次出动的无人机生成唯一ID
		drone_id = f"UAV-{drone_counter:03d}"

		# 存储该无人机的详细信息
		drone_fleet[drone_id] = {
			'model': best_drone['model'],
			'average_speed_mps': best_drone['average_speed_mps'],
			'flight_duration_s': best_drone['flight_duration_s'],
			'scan_width_m': best_drone['scan_width_m']
		}

		drone_counter += 1

	print(f"任务规划完成。总共需要 {len(drone_fleet)} 架次无人机。")
	print(f"预计总覆盖面积: {total_coverage_sq_m / 1_000_000:.2f} 平方公里。")

	return drone_fleet


# --- 主程序执行示例 ---
if __name__ == "__main__":
	# 设定需要观测的面积为 50 平方公里
	target_area = 50

	print(f"正在为 {target_area} 平方公里的区域规划无人机...")

	# 调用函数查找无人机组合
	selected_drones = find_drone_combination(target_area)

	print(selected_drones)

	# 打印结果
	if selected_drones:
		print("\n--- 选定的无人机组合 ---")
		for uav_id, details in selected_drones.items():
			print(f"  ID: {uav_id}, 型号: {details['model']}")
		print("--------------------------")
	else:
		print("未能生成无人机组合。")

