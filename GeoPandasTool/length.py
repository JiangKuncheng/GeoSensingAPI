import geopandas as gpd
import json
from shapely.geometry import shape


def length(geojson_str):
    """
    计算 Overpass API 导出的 GeoJSON 中每个 geometry 的长度

    参数:
        geojson_str (str): Overpass API 返回的 GeoJSON 字符串

    返回:
        list: 每个 geometry 的长度
    """
    # 解析 geojson
    geojson = json.loads(geojson_str)

    # 提取所有 geometry
    geometries = []
    if geojson.get("type") == "FeatureCollection":
        for feature in geojson["features"]:
            geom = shape(feature["geometry"])
            geometries.append(geom)
    elif geojson.get("type") == "Feature":
        geom = shape(geojson["geometry"])
        geometries.append(geom)
    else:
        raise ValueError("输入的 GeoJSON 不包含 Feature 或 FeatureCollection")

    if not geometries:
        raise ValueError("GeoJSON 中未找到有效的 geometry")

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算长度
    return gseries.length.tolist()
