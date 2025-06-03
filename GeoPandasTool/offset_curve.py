import geopandas as gpd
import json
from shapely.geometry import shape


def offset_curve(geojson_str, distance, side='right', resolution=16, join_style=1, mitre_limit=5.0):
    """
    为 Overpass API 获取的 LineString/MultiLineString 几何体生成 offset curve

    参数:
        geojson_str (str): Overpass API 返回的 GeoJSON 字符串
        distance (float): 偏移距离
        side (str): 'left' 或 'right'，偏移的方向 默认right
        resolution (int): 圆弧分割精度 默认16
        join_style (int): 连接样式，1=round, 2=mitre, 3=bevel 默认1
        mitre_limit (float): miter 连接样式时的限制 默认5.0

    返回:
        list: 偏移后的 geometry 的 WKT 表达形式（方便查看）
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

    # 只对 LineString 或 MultiLineString 有意义
    valid_types = ["LineString", "MultiLineString"]
    if not all(geom.geom_type in valid_types for geom in gseries):
        raise ValueError("offset_curve 只能用于 LineString 或 MultiLineString 类型")

    # 计算 offset curve
    result = gseries.offset_curve(distance=distance, side=side, resolution=resolution, join_style=join_style,
                                  mitre_limit=mitre_limit)

    return [geom.wkt for geom in result]
