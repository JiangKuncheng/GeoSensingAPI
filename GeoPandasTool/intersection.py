import geopandas as gpd
import json
from shapely.geometry import shape

def intersection(geojson_str, clip_geojson_str):
    """
    计算 Overpass API 获取的 GeoJSON 数据与另一个几何对象的交集 (intersection)。

    参数:
        geojson_str (str): 需要计算交集的 GeoJSON 字符串
        clip_geojson_str (str): 用于计算交集的 GeoJSON 字符串

    返回:
        str: 计算交集后的 GeoJSON 字符串
    """
    # 解析 GeoJSON
    geojson = json.loads(geojson_str)
    clip_geojson = json.loads(clip_geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson["features"]]
    clip_geometries = [shape(feature["geometry"]) for feature in clip_geojson["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)
    clip_series = gpd.GeoSeries(clip_geometries)

    # 计算交集（intersection）
    intersect_gseries = gseries.intersection(clip_series.unary_union)  # 计算所有几何对象的交集

    # 生成新的 GeoJSON 结果
    intersect_features = []
    for i, geom in enumerate(intersect_gseries):
        if not geom.is_empty:  # 仅保留交集后仍有数据的对象
            intersect_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": geojson["features"][i].get("properties", {})  # 保留原始属性
            })

    intersect_geojson = {
        "type": "FeatureCollection",
        "features": intersect_features
    }

    return json.dumps(intersect_geojson, indent=2)
