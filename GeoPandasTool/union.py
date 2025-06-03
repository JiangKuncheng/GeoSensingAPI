import geopandas as gpd
import json
from shapely.geometry import shape

def union(geojson_str1, geojson_str2):
    """
    计算 Overpass API 获取的两个 GeoJSON 数据的并集（union）。

    参数:
        geojson_str1 (str): 第一个 GeoJSON 字符串
        geojson_str2 (str): 第二个 GeoJSON 字符串

    返回:
        str: 计算并集后的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson1 = json.loads(geojson_str1)
    geojson2 = json.loads(geojson_str2)

    # 提取几何对象
    geometries1 = [shape(feature["geometry"]) for feature in geojson1["features"]]
    geometries2 = [shape(feature["geometry"]) for feature in geojson2["features"]]

    # 构建 GeoSeries
    gseries1 = gpd.GeoSeries(geometries1)
    gseries2 = gpd.GeoSeries(geometries2)

    # 计算并集
    union_gseries = gseries1.union(gseries2)

    # 生成新的 GeoJSON 结果
    union_features = []
    for geom in union_gseries:
        if not geom.is_empty:  # 仅保留非空对象
            union_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": {}  # 可根据需要添加属性
            })

    union_geojson = {
        "type": "FeatureCollection",
        "features": union_features
    }

    return json.dumps(union_geojson, indent=2)
