import geopandas as gpd
import json
from shapely.geometry import shape

def geom_almost_equal(geojson_str, other_geojson_str, tolerance=1e-9):
    """
    判断 Overpass API 获取的 GeoJSON 中的几何对象是否与另一个几何对象几乎相等（在容差范围内）

    参数:
        geojson_str (str): 主 GeoJSON 字符串
        other_geojson_str (str): 目标 GeoJSON 字符串，判断主几何是否与该几何几乎相等
        tolerance (float): 容差范围，用于判断几何是否几乎相等

    返回:
        list: 每个 geometry 是否与目标 geometry 几乎相等的布尔值
    """
    # 解析 geojson
    geojson = json.loads(geojson_str)
    other_geojson = json.loads(other_geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson["features"]]
    other_geometries = [shape(feature["geometry"]) for feature in other_geojson["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 检查是否几乎相等（在容差范围内）
    result = []
    for geometry in gseries:
        result.append(any(geometry.equals_exact(other_geometry, tolerance) for other_geometry in other_geometries))

    return result
