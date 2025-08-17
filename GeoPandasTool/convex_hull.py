import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def convex_hull(geojson_str):
    """
    计算 Overpass API 获取的 GeoJSON 数据的凸包（convex hull）。

    参数:
        geojson_str (str): GeoJSON 字符串

    返回:
        str: 凸包的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算凸包
    convex_hull_gseries = gseries.unary_union.convex_hull

    # 生成新的 GeoJSON 结果
    convex_hull_features = []
    if not convex_hull_gseries.is_empty:  # 仅保留非空对象
        convex_hull_features.append({
            "type": "Feature",
            "geometry": mapping(convex_hull_gseries),
            "properties": {}  # 可根据需要添加属性
        })

    convex_hull_geojson = {
        "type": "FeatureCollection",
        "features": convex_hull_features
    }

    return json.dumps(convex_hull_geojson, indent=2)
