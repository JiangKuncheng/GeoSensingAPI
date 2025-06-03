import geopandas as gpd
import json
from shapely.geometry import shape

def symmetric_difference(geojson_str, clip_geojson_str):
    """
    计算 Overpass API 获取的 GeoJSON 数据与另一个几何对象的对称差 (symmetric_difference)。

    参数:
        geojson_str (str): 需要计算对称差的 GeoJSON 字符串
        clip_geojson_str (str): 用于计算对称差的 GeoJSON 字符串

    返回:
        str: 计算对称差后的 GeoJSON 字符串
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

    # 计算对称差（symmetric_difference）
    sym_diff_gseries = gseries.symmetric_difference(clip_series.unary_union)  # 计算非重叠部分

    # 生成新的 GeoJSON 结果
    sym_diff_features = []
    for i, geom in enumerate(sym_diff_gseries):
        if not geom.is_empty:  # 仅保留非空对象
            sym_diff_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": geojson["features"][i].get("properties", {})  # 保留原始属性
            })

    sym_diff_geojson = {
        "type": "FeatureCollection",
        "features": sym_diff_features
    }

    return json.dumps(sym_diff_geojson, indent=2)
