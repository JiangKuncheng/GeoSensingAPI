import geopandas as gpd
import json
from shapely.geometry import shape, Polygon, MultiPolygon


def exterior(geojson_str):
    """
    提取 Overpass API 获取的 GeoJSON 数据中的 Polygon / MultiPolygon 的外边界

    参数:
        geojson_str (str): Overpass API 返回的 GeoJSON 字符串

    返回:
        list: 每个 Polygon / MultiPolygon 的外边界 (LineString)，其余类型返回 None
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

    # 提取 exterior，非 Polygon/MultiPolygon 返回 None
    exteriors = []
    for geom in gseries:
        if geom.geom_type == 'Polygon':
            exteriors.append(geom.exterior)
        elif geom.geom_type == 'MultiPolygon':
            exteriors.append([poly.exterior for poly in geom.geoms])
        else:
            exteriors.append(None)

    return exteriors
