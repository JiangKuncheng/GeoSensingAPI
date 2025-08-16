import sys
import json  # 新增: 导入json库
from SPARQLWrapper import SPARQLWrapper, JSON
from typing import List

from satelliteTool.get_TLE_data import get_tle


def execute_sparql_query(endpoint_url: str, query: str) -> List[dict]:
	"""
	连接到指定的SPARQL端点，执行查询，并返回一个解析后的结果列表。

	:param endpoint_url: 知识图谱的SPARQL端点URL。
	:param query: 要执行的SPARQL查询字符串。
	:return: 一个结果列表。列表中的每一项都是一个字典，
		 代表结果中的一行，键是变量名，值是对应的值。
		 查询失败或无结果时返回空列表。
	"""
	print(f"--- 正在查询端点: {endpoint_url} ---")
	try:
		sparql = SPARQLWrapper(endpoint_url)
		sparql.setQuery(query)
		sparql.setReturnFormat(JSON)

		# 执行查询并获取原始结果
		raw_results = sparql.query().convert()

		# 解析结果，将其转换为更友好的格式
		variables = raw_results.get("head", {}).get("vars", [])
		bindings = raw_results.get("results", {}).get("bindings", [])

		parsed_results = []
		for row in bindings:
			parsed_row = {}
			for var in variables:
				# 提取每个变量的值
				parsed_row[var] = row.get(var, {}).get("value")
			parsed_results.append(parsed_row)

		print("--- 查询成功 ---")
		return parsed_results

	except Exception as e:
		print(f"!!! 查询出错: {e}", file=sys.stderr)
		print("请确认端点URL是否正确，以及GraphDB服务是否已启动。", file=sys.stderr)
		return []


def get_satellite_names(endpoint_url: str) -> List[str]:
	"""
	查询指定端点上的所有卫星，并返回一个只包含卫星名称的列表。
	这个函数封装了查询逻辑和结果处理逻辑。

	:param endpoint_url: 知识图谱的SPARQL端点URL。
	:return: 一个包含卫星名称字符串的列表 (例如: ['Worldview_4', 'X_Sat'])。
		   如果查询失败或没有结果，则返回一个空列表。
	"""
	print("\n--- 正在准备查询所有卫星名称 ---")
	# 1. 定义用于查找所有卫星的SPARQL查询
	satellite_query = """
   PREFIX si: <http://sensorInformation/si/>
   SELECT ?satellite_uri WHERE {
     ?satellite_uri a si:Satellite .
   }
   """

	# 2. 调用核心函数执行查询
	results = execute_sparql_query(endpoint_url, satellite_query)

	# 3. 处理返回的结果
	if not results:
		return []

	# 从字典列表中提取URI值
	uri_list = [row.get('satellite_uri', '') for row in results]

	# 对每个URI进行处理，只保留最后的名称
	processed_names = [uri.rsplit('/', 1)[-1] for uri in uri_list if uri]

	print("--- 名称处理完成 ---")
	return processed_names


if __name__ == '__main__':

	print("--- 这是 sparql_utils.py 的使用演示 ---")

	# --- 1. 配置您的GraphDB SPARQL端点地址 ---
	my_endpoint = "http://localhost:7200/repositories/satellite"

	# --- 2. 调用封装的函数来获取处理后的卫星名称列表 ---
	satellite_names = get_satellite_names(my_endpoint)

	# --- 3. 获取TLE数据 ---
	# 如果 `satellite_names` 为空, get_tle 应该能处理这种情况并返回空列表
	tle_data = get_tle(satellite_names)

	print(tle_data)

	# --- 4. 新增: 将获取的 TLE 数据保存为 JSON 文件 ---
	if tle_data:
		output_filename = 'tle_data.json'
		print(f"\n--- 正在将 TLE 数据保存到 {output_filename} ---")
		try:
			# 使用 'w' 模式打开文件进行写入
			# encoding='utf-8' 确保正确处理中文字符
			with open(output_filename, 'w', encoding='utf-8') as f:
				# json.dump() 将 Python 对象序列化为 JSON 格式并写入文件
				# indent=4 使文件内容自动缩进，更易读
				# ensure_ascii=False 允许将中文字符直接写入文件，而不是作为 ASCII 转义序列
				json.dump(tle_data, f, ensure_ascii=False, indent=4)

			print(f"--- 数据已成功保存到: {output_filename} ---")
		except Exception as e:
			print(f"!!! 保存JSON文件时出错: {e}", file=sys.stderr)
	else:
		print("\n未获取到 TLE 数据或数据为空，无需保存文件。")