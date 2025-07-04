import geopandas as gpd
import json
from shapely.geometry import shape

def is_valid_reason(geojson_str):
    """
    返回 Overpass API 获取的 GeoJSON 中的每个 geometry 的合法性检查原因

    参数:
        geojson_str (str): Overpass API 返回的 GeoJSON 字符串

    返回:
        list: 每个 geometry 的合法性检查结果说明 (str)
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

    # 调用 is_valid_reason
    return gseries.is_valid_reason().tolist()
