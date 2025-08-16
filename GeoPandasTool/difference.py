import geopandas as gpd
import json
from shapely.geometry import shape

def difference(geojson_str, clip_geojson_str):
    """
    计算 Overpass API 获取的 GeoJSON 数据与另一个几何对象的差集 (difference)。

    参数:
        geojson_str (str): 需要计算差集的 GeoJSON 字符串 (被裁剪的对象)
        clip_geojson_str (str): 用于裁剪的 GeoJSON 字符串 (要移除的对象)

    返回:
        str: 计算差集后的 GeoJSON 字符串
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

    # 计算差集（difference）
    diff_gseries = gseries.difference(clip_series.unary_union)  # 将 clip_series 合并为单一几何对象

    # 生成新的 GeoJSON 结果
    diff_features = []
    for i, geom in enumerate(diff_gseries):
        if not geom.is_empty:  # 仅保留差集后仍有数据的对象
            diff_features.append({
                "type": "Feature",
                "geometry": geom.__geo_interface__,
                "properties": geojson["features"][i].get("properties", {})  # 保留原始属性
            })

    diff_geojson = {
        "type": "FeatureCollection",
        "features": diff_features
    }

    return json.dumps(diff_geojson, indent=2)
