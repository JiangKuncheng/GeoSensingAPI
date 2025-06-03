import geopandas as gpd
import json
from shapely.geometry import shape, mapping

def line_merge(geojson_str):
    """
    合并 Overpass API 获取的 GeoJSON 数据中的 LineString 线段。

    参数:
        geojson_str (str): GeoJSON 字符串。

    返回:
        str: 线段合并后的 GeoJSON 字符串。
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取 LineString 类型的几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]
                  if feature["geometry"]["type"] == "LineString"]

    # 如果没有 LineString，直接返回空的 GeoJSON
    if not geometries:
        return json.dumps({"type": "FeatureCollection", "features": []}, indent=2)

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 进行线合并
    merged_lines = gseries.line_merge()

    # 生成新的 GeoJSON 结果
    merged_features = []
    for geom in merged_lines:
        if not geom.is_empty:  # 仅保留非空对象
            merged_features.append({
                "type": "Feature",
                "geometry": mapping(geom),
                "properties": {}  # 可根据需要添加属性
            })

    merged_geojson = {
        "type": "FeatureCollection",
        "features": merged_features
    }

    return json.dumps(merged_geojson, indent=2)
