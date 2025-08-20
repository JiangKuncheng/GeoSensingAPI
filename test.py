import folium
import geopandas


def create_interactive_map(geojson_file: str, output_html: str):
	"""
	读取GeoJSON文件并创建一个交互式的Folium地图。

	:param geojson_file: 输入的GeoJSON文件路径。
	:param output_html: 输出的HTML地图文件路径。
	"""
	print(f"正在读取地理数据: {geojson_file}")
	gdf = geopandas.read_file(geojson_file)

	# --- 核心修复代码 ---
	# 将Timestamp对象列显式转换为字符串，以确保JSON序列化成功。
	if 'timestamp' in gdf.columns:
		gdf['timestamp'] = gdf['timestamp'].astype(str)
	# --------------------

	try:
		center_lat = gdf.unary_union.centroid.y
		center_lon = gdf.unary_union.centroid.x
		m = folium.Map(location=[center_lat, center_lon], zoom_start=2)
	except Exception:
		print("无法计算中心点，使用默认全球视图。")
		m = folium.Map(location=[30, 0], zoom_start=2)

	print("正在向地图添加卫星足迹图层...")

	popup = folium.GeoJsonPopup(
		fields=['satellite', 'timestamp'],
		aliases=['卫星 (Satellite):', '时间 (Timestamp):'],
		localize=True,
		style="background-color: yellow;",
	)

	style_function = lambda x: {
		"fillColor": "#3186cc",
		"color": "blue",
		"weight": 1,
		"fillOpacity": 0.2,
	}

	folium.GeoJson(
		gdf,
		style_function=style_function,
		popup=popup,
		name='卫星覆盖范围 (Satellite Coverage)'
	).add_to(m)

	folium.LayerControl().add_to(m)

	print(f"正在保存地图到: {output_html}")
	m.save(output_html)
	print(f"✅ 地图已成功生成！请在浏览器中打开 '{output_html}' 查看。")


if __name__ == '__main__':
	# 你的GeoJSON文件名
	input_geojson = "satellite_coverage_2025-08-01.geojson"
	# 定义输出的HTML文件名
	output_map_file = "interactive_satellite_map.html"

	create_interactive_map(input_geojson, output_map_file)