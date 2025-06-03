import geopandas as gpd
import json
from shapely.geometry import shape

def within(geojson_str, container_geojson_str):
    """
    判断 Overpass API 获取的 GeoJSON 数据中的几何对象是否完全包含在另一个几何对象内部。

    参数:
        geojson_str (str): 需要判断的 GeoJSON 字符串
        container_geojson_str (str): 作为容器的 GeoJSON 字符串

    返回:
        list: 每个 geometry 是否在 container geometry 内部的布尔值
    """
    # 解析 GeoJSON
    geojson = json.loads(geojson_str)
    container_geojson = json.loads(container_geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson["features"]]
    container_geometries = [shape(feature["geometry"]) for feature in container_geojson["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)
    container_series = gpd.GeoSeries(container_geometries)

    # 判断是否完全包含在另一个几何对象内部
    result = []
    for geometry in gseries:
        result.append(any(geometry.within(container) for container in container_series))

    return result
