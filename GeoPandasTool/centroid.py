import geopandas as gpd
import json
from shapely.geometry import shape

def centroid(geojson_str):
    """
    计算 Overpass API 获取的 GeoJSON 数据的质心（centroid）。

    参数:
        geojson_str (str): GeoJSON 字符串

    返回:
        str: 质心的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算质心
    centroids = gseries.centroid

    # 生成新的 GeoJSON 结果
    centroid_features = []
    for geom in centroids:
        if not geom.is_empty:  # 仅保留非空对象
            centroid_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": {}  # 可根据需要添加属性
            })

    centroid_geojson = {
        "type": "FeatureCollection",
        "features": centroid_features
    }

    return json.dumps(centroid_geojson, indent=2)
