import geopandas as gpd
import json
from shapely.geometry import shape

def is_ring(geojson_str):
    """
    判断 Overpass API 获取的 GeoJSON 中的 LineString 几何对象是否是 ring（闭合且简单）

    参数:
        geojson_str (str): Overpass API 返回的 GeoJSON 字符串

    返回:
        list: 每个 geometry 的 is_ring 布尔值
    """
    # 解析 geojson
    geojson = json.loads(geojson_str)
    geometries = []

    if geojson.get("type") == "FeatureCollection":
        for feature in geojson["features"]:
            geometries.append(shape(feature["geometry"]))
    elif geojson.get("type") == "Feature":
        geometries.append(shape(geojson["geometry"]))
    else:
        raise ValueError("输入的 GeoJSON 不包含 Feature 或 FeatureCollection")

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 调用 is_ring
    return gseries.is_ring.tolist()
