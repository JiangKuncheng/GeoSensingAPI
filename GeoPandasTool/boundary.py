import geopandas as gpd
import json
from shapely.geometry import shape


def boundary(*geojson_strs, multiInvocation=False, times=1):
    """
    计算一个或多个 Overpass API 导出的 GeoJSON 的边界

    参数:
        *geojson_strs (str): 一个或多个 GeoJSON 字符串
        multiInvocation (bool): 是否启用多次调用模式
        times (int): 如果启用多次调用模式，指定 GeoJSON 的数量

    返回:
        list[geopandas.GeoSeries] | geopandas.GeoSeries:
            如果 multiInvocation 为 True，返回每个 GeoJSON 的边界列表；
            否则返回单个 GeoJSON 的边界 GeoSeries。
    """
    if multiInvocation:
        if len(geojson_strs) != times:
            raise ValueError("提供的 GeoJSON 数量与 times 参数不匹配")

        boundaries = []
        for geojson_str in geojson_strs:
            geojson = json.loads(geojson_str)
            geometries = _extract_geometries(geojson)
            gseries = gpd.GeoSeries(geometries)
            boundaries.append(gseries.boundary)
        return boundaries
    else:
        if len(geojson_strs) != 1:
            raise ValueError("未启用 multiInvocation 时仅能传入一个 GeoJSON")

        geojson = json.loads(geojson_strs[0])
        geometries = _extract_geometries(geojson)
        gseries = gpd.GeoSeries(geometries)
        return gseries.boundary


def _extract_geometries(geojson):
    geometries = []
    if geojson.get("type") == "FeatureCollection":
        for feature in geojson["features"]:
            geom = shape(feature["geometry"])
            if geom.geom_type in ["Polygon", "MultiPolygon"]:
                geometries.append(geom)
    elif geojson.get("type") == "Feature":
        geom = shape(geojson["geometry"])
        if geom.geom_type in ["Polygon", "MultiPolygon"]:
            geometries.append(geom)

    if not geometries:
        raise ValueError("未找到 Polygon 或 MultiPolygon")
    return geometries