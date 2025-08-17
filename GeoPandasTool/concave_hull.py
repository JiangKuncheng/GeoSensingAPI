import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

def concave_hull(geojson_str, alpha=0.05):
    """
    计算 Overpass API 获取的 GeoJSON 数据的凹壳（concave hull）。

    参数:
        geojson_str (str): GeoJSON 字符串
        alpha (float): 影响凹壳形状的参数，越小越精细，越大越简洁

    返回:
        str: 凹壳的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算凹壳
    concave_hull_gseries = gseries.unary_union.convex_hull

    # 生成新的 GeoJSON 结果
    concave_hull_features = []
    if not concave_hull_gseries.is_empty:  # 仅保留非空对象
        concave_hull_features.append({
            "type": "Feature",
            "geometry": mapping(concave_hull_gseries),
            "properties": {}  # 可根据需要添加属性
        })

    concave_hull_geojson = {
        "type": "FeatureCollection",
        "features": concave_hull_features
    }

    return json.dumps(concave_hull_geojson, indent=2)
