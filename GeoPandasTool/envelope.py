import geopandas as gpd
import json
from shapely.geometry import shape

def envelope(geojson_str):
    """
    计算 Overpass API 获取的 GeoJSON 数据的外包络矩形。

    参数:
        geojson_str (str): GeoJSON 字符串

    返回:
        str: 外包络矩形的 GeoJSON 字符串
    """
    # 解析 GeoJSON 数据
    geojson_data = json.loads(geojson_str)

    # 提取几何对象
    geometries = [shape(feature["geometry"]) for feature in geojson_data["features"]]

    # 构建 GeoSeries
    gseries = gpd.GeoSeries(geometries)

    # 计算外包络矩形
    envelope_gseries = gseries.envelope

    # 生成新的 GeoJSON 结果
    envelope_features = []
    for geom in envelope_gseries:
        if not geom.is_empty:  # 仅保留非空对象
            envelope_features.append({
                "type": "Feature",
                "geometry": json.loads(geom.to_json()),
                "properties": {}  # 可根据需要添加属性
            })

    envelope_geojson = {
        "type": "FeatureCollection",
        "features": envelope_features
    }

    return json.dumps(envelope_geojson, indent=2)
