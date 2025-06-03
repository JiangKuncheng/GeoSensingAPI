import geopandas as gpd
import json
from shapely.geometry import shape

def touches(geojson_str, other_geojson_str):
    """
    判断 Overpass API 获取的 GeoJSON 数据中的几何对象是否仅在边界上接触目标几何对象。

    参数:
        geojson_str (str): 主 GeoJSON 字符串
        other_geojson_str (str): 目标 GeoJSON 字符串，判断主几何是否与其接触

    返回:
        list: 每个 geometry 是否仅在边界上接触目标 geometry 的布尔值
    """
    # 解析 GeoJSON
    geojson = json.loads(geojson_str)
    other_geojson = json.loads(other_geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson["features"]]
    other_geometries = [shape(feature["geometry"]) for feature in other_geojson["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)
    other_series = gpd.GeoSeries(other_geometries)

    # 判断是否仅在边界上接触
    result = []
    for geometry in gseries:
        result.append(any(geometry.touches(other) for other in other_series))

    return result
