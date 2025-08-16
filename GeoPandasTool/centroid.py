import geopandas as gpd
import json
from shapely.geometry import shape
from shapely.geometry import mapping

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
            try:
                centroid_features.append({
                    "type": "Feature",
                    "geometry": mapping(geom),
                    "properties": {}  # 可根据需要添加属性
                })
            except Exception as e:
                # 如果单个几何对象处理失败，跳过
                continue

    centroid_geojson = {
        "type": "FeatureCollection",
        "features": centroid_features
    }

    return json.dumps(centroid_geojson, indent=2)
