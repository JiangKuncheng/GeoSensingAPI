import geopandas as gpd
import json
from shapely.geometry import shape


def total_bounds(geojson_str):
    """
    计算Overpass API导出的GeoJSON中所有geometry的整体包围盒

    参数:
        geojson_str (str): Overpass API返回的GeoJSON字符串

    返回:
        list: [minx, miny, maxx, maxy]
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
        raise ValueError("输入的GeoJSON不包含Feature或FeatureCollection")

    if not geometries:
        raise ValueError("GeoJSON中未找到有效的geometry")

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算 total_bounds
    return gseries.total_bounds.tolist()
