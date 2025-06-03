import geopandas as gpd
import json
from shapely.geometry import shape

def intersects(geojson_str, other_geojson_str):
    """
    判断 Overpass API 获取的 GeoJSON 中的几何对象是否与另一个几何对象相交

    参数:
        geojson_str (str): 主 GeoJSON 字符串
        other_geojson_str (str): 目标 GeoJSON 字符串，判断主几何是否与该几何相交

    返回:
        list: 每个 geometry 是否与目标 geometry 相交的布尔值
    """
    # 解析 geojson
    geojson = json.loads(geojson_str)
    other_geojson = json.loads(other_geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson["features"]]
    other_geometries = [shape(feature["geometry"]) for feature in other_geojson["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 检查是否相交
    result = []
    for geometry in gseries:
        result.append(any(geometry.intersects(other_geometry) for other_geometry in other_geometries))

    return result
